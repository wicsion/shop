from django.core.management.base import BaseCommand
from main.models import XMLProduct, ProductVariant, ProductVariantThrough
from xml.etree import ElementTree as ET
import requests
import logging
import time
from tqdm import tqdm
from django.db import transaction
from django.db.models import Q
from pyrate_limiter import Duration, Rate, Limiter


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimized product quantities update from stock.xml with rate limiting'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.auth = ('87358_xmlexport', 'MGzXXSgD')
        self.size_mapping = {
            'XS': 'XS', 'S': 'S', 'M': 'M', 'L': 'L', 'XL': 'XL',
            'XXL': 'XXL', 'XXXL': 'XXXL', '3XL': 'XXXL', '4XL': '4XL', '5XL': '5XL'
        }
        self.product_code_map = {}
        self.product_id_map = {}
        self.last_request_time = 0
        self.min_interval = 0.2  # 5 requests per second = 1 request every 0.2 seconds
        # Инициализация rate limiter
        self.rate = Rate(5, Duration.SECOND)  # 5 запросов в секунду
        self.limiter = Limiter(self.rate) # 5 запросов в секунду


    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=1000,
                          help='Batch size for DB operations')
        parser.add_argument('--max-retries', type=int, default=3,
                          help='Max retries for failed requests')

    def handle(self, *args, **options):
        stock_url = "https://api2.gifts.ru/export/v2/catalogue/stock.xml"

        try:
            # 1. Build product lookup maps
            self.build_product_maps()

            # 2. Download and parse stock data with rate limiting
            stock_data = self.download_and_parse_stock(stock_url, options['max_retries'])

            # 3. Process updates
            self.process_updates(stock_data, options['batch_size'])

            logger.info("Quantity update completed successfully")

        except Exception as e:
            logger.error(f"Fatal error: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def rate_limited_request(self):
        """Ограничение запросов с ожиданием"""
        while True:
            try:
                self.limiter.try_acquire("api_request")
                break
            except:
                # Если лимит превышен, ждем 0.2 секунды перед повторной попыткой
                time.sleep(0.2)

    def build_product_maps(self):
        """Build in-memory maps for product lookup"""
        logger.info("Building product lookup maps...")
        products = XMLProduct.objects.all().only(
            'id', 'product_id', 'code', 'price', 'old_price', 'quantity', 'in_stock'
        )

        # Create maps for both product_id and code
        self.product_id_map = {p.product_id: p for p in products}
        self.product_code_map = {p.code: p for p in products}

        logger.info(f"Created maps for {len(products)} products")

    def download_and_parse_stock(self, url, max_retries):
        """Download and parse stock data with retries and rate limiting"""
        for attempt in range(max_retries):
            try:
                self.rate_limited_request()
                logger.info(f"Downloading stock data (attempt {attempt + 1})...")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                # Parse XML and process stock data
                root = ET.fromstring(response.content)
                return self.process_stock_data(root)

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = (attempt + 1) * 5
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            except ET.ParseError as e:
                logger.error(f"XML parsing error: {str(e)}")
                raise

    def process_stock_data(self, root):
        """Обработка данных о наличии"""
        stock_items = list(root.findall('stock'))
        stock_data = {}

        for item in tqdm(stock_items, desc="Processing stock items"):
            try:
                product_id = item.find('product_id').text.strip()
                code = item.find('code').text.strip()
                free = int(item.find('free').text)

                # Находим продукт
                product = (
                        self.product_id_map.get(product_id) or
                        self.product_code_map.get(code) or
                        self.find_product_by_alt_code(code)
                )

                if not product:
                    continue

                # Извлекаем размер из кода
                size = self.extract_size_from_code(code, product)

                if not size:
                    # Если размер не определен, используем основной продукт
                    if product.product_id not in stock_data:
                        stock_data[product.product_id] = {
                            'product': product,
                            'total_free': 0,
                            'variants': {}
                        }
                    stock_data[product.product_id]['total_free'] += free
                    continue

                # Обрабатываем вариант с размером
                if product.product_id not in stock_data:
                    stock_data[product.product_id] = {
                        'product': product,
                        'total_free': 0,
                        'variants': {}
                    }

                stock_data[product.product_id]['total_free'] += free
                stock_data[product.product_id]['variants'][size] = free

            except Exception as e:
                logger.debug(f"Skipping item: {str(e)}")
                continue

        return stock_data

    def find_product_by_alt_code(self, code):
        """Find product by alternative code patterns with rate limiting"""
        self.rate_limited_request()

        # Try to match code without size suffix
        for size in ['XXXL', 'XXL', 'XL', 'XS', 'S', 'M', 'L', '3XL', '4XL', '5XL']:
            if code.endswith(size):
                base_code = code[:-len(size)].rstrip()
                return self.product_code_map.get(base_code)

        # Try to find similar code in DB
        return XMLProduct.objects.filter(
            Q(code__startswith=code[:6]) |
            Q(code__contains=code[-4:])
        ).first()

    # В методе extract_size_from_code класса Command
    def extract_size_from_code(self, code, product):
        """Извлекаем размер из кода товара с полной фильтрацией"""
        # Список исключаемых терминов
        EXCLUDED_TERMS = [
            'hat', 'cap', 'head', 'cm', 'one size', 'размер', 'обхват',
            'головы', 'обуви', 'shoe', 'size', 'для', 'мужские', 'женские',
            'унисекс', 'male', 'female', 'unisex', 'детские', 'муж', 'жен',
            'м', 'ж', 'man', 'woman', 'men', 'women'
        ]

        # Удаляем числовые размеры (например, 42, 44, 46 и т.д.)
        if any(part.isdigit() for part in code.split('.')):
            return None

        # Удаляем размеры с "см"
        if 'cm' in code.lower() or 'см' in code.lower():
            return None

        parts = code.split('.')
        last_part = parts[-1].upper()

        # Проверяем стандартные размеры
        size_mapping = {
            'XS': 'XS', 'S': 'S', 'M': 'M', 'L': 'L', 'XL': 'XL',
            'XXL': 'XXL', 'XXXL': 'XXXL', '3XL': 'XXXL', '4XL': '4XL', '5XL': '5XL'
        }

        # Проверяем, является ли последняя часть размером (исключая запрещенные термины)
        for size_pattern in size_mapping:
            if size_pattern in last_part:
                # Проверяем, нет ли в размере исключенных терминов
                size_lower = size_pattern.lower()
                if not any(term.lower() in size_lower for term in EXCLUDED_TERMS):
                    return size_mapping[size_pattern]

        # Если размер не найден, проверяем предыдущую часть
        if len(parts) > 1:
            prev_part = parts[-2].upper()
            for size_pattern in size_mapping:
                if size_pattern in prev_part:
                    size_lower = size_pattern.lower()
                    if not any(term.lower() in size_lower for term in EXCLUDED_TERMS):
                        return size_mapping[size_pattern]

        return None

    # В методе process_updates добавить очистку старых вариантов перед созданием новых
    def process_updates(self, stock_data, batch_size):
        """Process all updates with batch optimization and clean old variants"""
        products_to_update = []
        variants_to_create = []
        through_to_create = []

        logger.info("Preparing updates...")

        # Сначала удаляем все существующие варианты для обновляемых товаров
        product_ids = [data['product'].id for data in stock_data.values()]
        ProductVariantThrough.objects.filter(product_id__in=product_ids).delete()
        ProductVariant.objects.filter(product_id__in=product_ids).delete()

        for product_id, data in tqdm(stock_data.items(), desc="Preparing data"):
            product = data['product']
            product.quantity = data['total_free']
            product.in_stock = data['total_free'] > 0
            products_to_update.append(product)

            for size, quantity in data['variants'].items():
                # Пропускаем пустые размеры
                if not size:
                    continue

                variant = ProductVariant(
                    product_id=product.id,  # Явно устанавливаем связь
                    size=size,
                    quantity=quantity,
                    price=product.price,
                    old_price=product.old_price,
                    sku=f"{product.code}-{size}"
                )
                variants_to_create.append(variant)
                through_to_create.append({
                    'product_id': product.id,
                    'variant_sku': variant.sku,
                    'quantity': quantity,
                    'price': product.price,
                    'old_price': product.old_price
                })

        # Остальной код метода остается без изменений...
        logger.info("Executing bulk updates...")
        with transaction.atomic():
            # Update products
            if products_to_update:
                XMLProduct.objects.bulk_update(
                    products_to_update,
                    ['quantity', 'in_stock'],
                    batch_size=batch_size
                )
                logger.info(f"Updated {len(products_to_update)} products")

            # Create variants
            if variants_to_create:
                created_variants = ProductVariant.objects.bulk_create(
                    variants_to_create,
                    batch_size=batch_size
                )
                logger.info(f"Created {len(created_variants)} variants")

                # Create through relations
                if through_to_create:
                    variant_map = {v.sku: v for v in created_variants}
                    through_objects = [
                        ProductVariantThrough(
                            product_id=item['product_id'],
                            variant_id=variant_map[item['variant_sku']].id,
                            quantity=item['quantity'],
                            price=item['price'],
                            old_price=item['old_price']
                        )
                        for item in through_to_create
                        if item['variant_sku'] in variant_map
                    ]

                    ProductVariantThrough.objects.bulk_create(
                        through_objects,
                        batch_size=batch_size
                    )
                    logger.info(f"Created {len(through_objects)} through relations")

