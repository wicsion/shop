from django.core.management.base import BaseCommand
from main.models import XMLProduct, ProductVariant, ProductVariantThrough, Category
from xml.etree import ElementTree as ET
import requests
import logging
import time
from tqdm import tqdm
from django.db import transaction
from django.db.models import Q
import re

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimized product quantities update from stock.xml with size separation'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.auth = ('87358_xmlexport', 'MGzXXSgD')
        self.size_mapping = {
            'XS': 'XS', 'S': 'S', 'M': 'M', 'L': 'L', 'XL': 'XL',
            'XXL': 'XXL', 'XXXL': 'XXXL', '3XL': 'XXXL', '4XL': '4XL', '5XL': '5XL'
        }
        self.clothing_category_ids = set()

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=1000)
        parser.add_argument('--max-retries', type=int, default=3)

    def handle(self, *args, **options):
        # Предварительно загружаем ID категорий одежды
        self.load_clothing_categories()

        stock_url = "https://api2.gifts.ru/export/v2/catalogue/stock.xml"
        try:
            self.build_product_maps()
            stock_data = self.download_and_parse_stock(stock_url, options['max_retries'])
            self.process_updates(stock_data, options['batch_size'])
            logger.info("Quantity update completed successfully")
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}", exc_info=True)

    def load_clothing_categories(self):
        """Загружаем ID категорий одежды для быстрой проверки"""
        clothing_categories = Category.objects.filter(
            Q(name__icontains='одежда') |
            Q(name__icontains='футболк') |
            Q(name__icontains='толстовк') |
            Q(name__icontains='текстиль')
        )
        self.clothing_category_ids = {c.id for c in clothing_categories}

    def is_clothing_product(self, product):
        """Проверяем, относится ли товар к одежде"""
        return any(cat.id in self.clothing_category_ids for cat in product.categories.all())

    def extract_size_from_code(self, code, product):
        """Извлекаем размер из кода товара с учетом типа товара"""
        if self.is_clothing_product(product):
            # Для одежды ищем стандартные размеры
            parts = code.split('.')
            last_part = parts[-1].upper()

            for size_pattern in self.size_mapping:
                if size_pattern in last_part:
                    return self.size_mapping[size_pattern]

            if len(parts) > 1:
                prev_part = parts[-2].upper()
                for size_pattern in self.size_mapping:
                    if size_pattern in prev_part:
                        return self.size_mapping[size_pattern]
        else:
            # Для не-одежды возвращаем None (габариты будем брать из других полей)
            return None

        return None

    def build_product_maps(self):
        """Создаем карту продуктов для быстрого поиска"""
        products = XMLProduct.objects.all().only(
            'id', 'product_id', 'code', 'price', 'old_price', 'quantity', 'in_stock'
        ).prefetch_related('categories')

        self.product_id_map = {p.product_id: p for p in products}
        self.product_code_map = {p.code: p for p in products}

    def download_and_parse_stock(self, url, max_retries):
        """Загрузка и парсинг XML с данными о наличии"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return self.process_stock_data(ET.fromstring(response.content))
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep((attempt + 1) * 5)

    def process_stock_data(self, root):
        """Обработка данных о наличии с разделением размеров и габаритов"""
        stock_items = list(root.findall('stock'))
        stock_data = {}

        for item in tqdm(stock_items, desc="Processing stock items"):
            try:
                product_id = item.find('product_id').text.strip()
                code = item.find('code').text.strip()
                free = int(item.find('free').text)

                product = (
                        self.product_id_map.get(product_id) or
                        self.product_code_map.get(code) or
                        self.find_product_by_alt_code(code)
                )

                if not product:
                    continue

                size = self.extract_size_from_code(code, product)

                if product.product_id not in stock_data:
                    stock_data[product.product_id] = {
                        'product': product,
                        'total_free': 0,
                        'variants': {},
                        'is_clothing': self.is_clothing_product(product)
                    }

                stock_data[product.product_id]['total_free'] += free

                if size:
                    if size not in stock_data[product.product_id]['variants']:
                        stock_data[product.product_id]['variants'][size] = 0
                    stock_data[product.product_id]['variants'][size] += free

            except Exception as e:
                logger.debug(f"Skipping item: {str(e)}")
                continue

        return stock_data

    def process_updates(self, stock_data, batch_size):
        """Обновление данных с учетом разделения размеров и габаритов"""
        products_to_update = []
        variants_to_create = []
        through_to_create = []

        for product_id, data in tqdm(stock_data.items(), desc="Preparing updates"):
            product = data['product']
            product.quantity = data['total_free']
            product.in_stock = data['total_free'] > 0

            # Для одежды обновляем clothing_sizes, для остальных - dimensions
            if data['is_clothing']:
                sizes = list(data['variants'].keys())
                product.clothing_sizes = ', '.join(sorted(sizes)) if sizes else None
            else:
                # Габариты берем из существующих данных или оставляем как есть
                pass

            products_to_update.append(product)

            # Создаем варианты только для одежды
            if data['is_clothing']:
                for size, quantity in data['variants'].items():
                    variant = ProductVariant(
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

        # Применяем обновления
        with transaction.atomic():
            if products_to_update:
                XMLProduct.objects.bulk_update(
                    products_to_update,
                    ['quantity', 'in_stock', 'clothing_sizes', 'dimensions'],
                    batch_size=batch_size
                )

            if variants_to_create:
                created_variants = ProductVariant.objects.bulk_create(
                    variants_to_create,
                    batch_size=batch_size
                )

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
                    ProductVariantThrough.objects.bulk_create(through_objects)

    def find_product_by_alt_code(self, code):
        """Поиск товара по альтернативным вариантам кода"""
        # Упрощенный поиск - в реальной реализации может быть сложнее
        return XMLProduct.objects.filter(
            Q(code__startswith=code[:6]) | Q(code__endswith=code[-4:])
        ).first()