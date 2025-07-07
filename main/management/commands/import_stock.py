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
    help = 'Optimized product quantities update from stock.xml with proper size handling'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.auth = ('87358_xmlexport', 'MGzXXSgD')
        self.size_mapping = {
            'XS': 'XS', 'S': 'S', 'M': 'M', 'L': 'L', 'XL': 'XL',
            'XXL': 'XXL', 'XXXL': 'XXXL', '3XL': 'XXXL', '4XL': '4XL', '5XL': '5XL'
        }
        self.clothing_category_ids = set()
        self.product_id_map = {}
        self.product_code_map = {}

    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=500,
                            help='Number of records to process in each batch')
        parser.add_argument('--max-retries', type=int, default=3,
                            help='Maximum number of retries for downloading stock data')
        parser.add_argument('--debug', action='store_true',
                            help='Enable debug output')

    def handle(self, *args, **options):
        if options['debug']:
            logging.basicConfig(level=logging.DEBUG)

        self.load_clothing_categories()
        stock_url = "https://api2.gifts.ru/export/v2/catalogue/stock.xml"

        try:
            self.build_product_maps()
            stock_data = self.download_and_parse_stock(stock_url, options['max_retries'])
            self.process_updates(stock_data, options['batch_size'])
            logger.info("Stock update completed successfully")
        except Exception as e:
            logger.error(f"Fatal error during stock update: {str(e)}", exc_info=True)
            raise

    def load_clothing_categories(self):
        """Load IDs of clothing-related categories"""
        clothing_categories = Category.objects.filter(
            Q(name__icontains='одежда') |
            Q(name__icontains='футболк') |
            Q(name__icontains='толстовк') |
            Q(name__icontains='текстиль') |
            Q(name__icontains='рубашк') |
            Q(name__icontains='кофт') |
            Q(name__icontains='свитер') |
            Q(name__icontains='худи')
        )
        self.clothing_category_ids = {c.id for c in clothing_categories}
        logger.debug(f"Loaded {len(self.clothing_category_ids)} clothing category IDs")

    def is_clothing_product(self, product):
        """Check if product belongs to clothing categories"""
        if not product:
            return False
        return any(cat.id in self.clothing_category_ids for cat in product.categories.all())

    def extract_size_from_code(self, code, product):
        """
        Extract size from product code with improved pattern matching
        Handles cases like:
        - '00548312L' (size at end)
        - '00548312-L' (size with separator)
        - '00548312XL' (multi-character size)
        - '005483123XL' (size with number prefix)
        """
        if not code or not self.is_clothing_product(product):
            return None

        # Try to match size patterns in the code
        code_upper = code.upper()

        # Check for size at the end of the code (most common case)
        for size_pattern in sorted(self.size_mapping.keys(), key=len, reverse=True):
            if code_upper.endswith(size_pattern):
                return self.size_mapping[size_pattern]

        # Check for size with separator (like '00548312-L')
        for size_pattern in sorted(self.size_mapping.keys(), key=len, reverse=True):
            if f"-{size_pattern}" in code_upper:
                return self.size_mapping[size_pattern]
            if f"_{size_pattern}" in code_upper:
                return self.size_mapping[size_pattern]

        # Check for size in the middle of the code (less common)
        for size_pattern in sorted(self.size_mapping.keys(), key=len, reverse=True):
            if size_pattern in code_upper and not code_upper.endswith(size_pattern):
                return self.size_mapping[size_pattern]

        return None

    def build_product_maps(self):
        """Build lookup maps for products by ID and code"""
        products = XMLProduct.objects.all().only(
            'id', 'product_id', 'code', 'price', 'old_price', 'quantity', 'in_stock'
        ).prefetch_related('categories')

        self.product_id_map = {p.product_id: p for p in products}
        self.product_code_map = {p.code: p for p in products}

        logger.info(f"Built product maps: {len(self.product_id_map)} by ID, {len(self.product_code_map)} by code")

    def download_and_parse_stock(self, url, max_retries):
        """Download and parse stock XML with retry logic"""
        for attempt in range(max_retries):
            try:
                start_time = time.time()
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                # Validate XML structure
                try:
                    root = ET.fromstring(response.content)
                    if root.tag != 'doct':
                        raise ValueError("Invalid XML root element, expected 'doct'")

                    logger.info(f"Downloaded and parsed stock XML in {time.time() - start_time:.2f}s")
                    return self.process_stock_data(root)

                except ET.ParseError as e:
                    logger.error(f"XML parsing error: {e}")
                    if attempt == max_retries - 1:
                        raise

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep((attempt + 1) * 5)

    def process_stock_data(self, root):
        """Process stock data from XML and organize by product with size variants"""
        stock_items = list(root.findall('stock'))
        stock_data = {}
        logger.info(f"Processing {len(stock_items)} stock items")

        for item in tqdm(stock_items, desc="Processing stock items"):
            try:
                product_id = item.find('product_id').text.strip() if item.find('product_id') is not None else None
                code = item.find('code').text.strip() if item.find('code') is not None else None
                free = int(item.find('free').text) if item.find('free') is not None else 0

                if not product_id or not code:
                    logger.debug(f"Skipping item with missing product_id or code: {ET.tostring(item)}")
                    continue

                # Find product by ID or code
                product = (
                        self.product_id_map.get(product_id) or
                        self.product_code_map.get(code) or
                        self.find_product_by_alt_code(code)
                )

                if not product:
                    logger.debug(f"Product not found for ID: {product_id} or code: {code}")
                    continue

                # Extract size for clothing products
                size = self.extract_size_from_code(code, product)
                is_clothing = self.is_clothing_product(product)

                # Initialize product entry if not exists
                if product.product_id not in stock_data:
                    stock_data[product.product_id] = {
                        'product': product,
                        'total_free': 0,
                        'variants': {},
                        'is_clothing': is_clothing
                    }

                # Update total quantity
                stock_data[product.product_id]['total_free'] += free

                # Update size variants for clothing
                if is_clothing and size:
                    if size not in stock_data[product.product_id]['variants']:
                        stock_data[product.product_id]['variants'][size] = 0
                    stock_data[product.product_id]['variants'][size] += free
                    logger.debug(f"Updated variant: {product.product_id} - {size}: {free}")

            except Exception as e:
                logger.warning(f"Error processing stock item: {str(e)}")
                continue

        return stock_data

    def process_updates(self, stock_data, batch_size):
        """Process updates in batches with proper variant handling"""
        products_to_update = []
        variants_to_create = []
        through_to_create = []

        logger.info(f"Preparing updates for {len(stock_data)} products")

        # First pass: prepare all updates
        for product_id, data in tqdm(stock_data.items(), desc="Preparing updates"):
            product = data['product']
            product.quantity = data['total_free']
            product.in_stock = data['total_free'] > 0

            # Handle clothing sizes
            if data['is_clothing']:
                sizes = list(data['variants'].keys())
                product.clothing_sizes = ', '.join(sorted(sizes)) if sizes else ''
                logger.debug(f"Product {product_id} sizes: {product.clothing_sizes}")

            products_to_update.append(product)

            # Prepare variants for clothing products
            if data['is_clothing'] and data['variants']:
                for size, quantity in data['variants'].items():
                    variant = ProductVariant(
                        size=size,
                        quantity=quantity,
                        price=product.price,
                        old_price=product.old_price,
                        sku=f"{product.code}-{size}" if product.code else f"{product_id}-{size}"
                    )
                    variants_to_create.append(variant)
                    through_to_create.append({
                        'product_id': product.id,
                        'variant_sku': variant.sku,
                        'quantity': quantity,
                        'price': product.price,
                        'old_price': product.old_price
                    })

        # Process updates in batches
        with transaction.atomic():
            # Update products in batches
            for i in range(0, len(products_to_update), batch_size):
                batch = products_to_update[i:i + batch_size]
                XMLProduct.objects.bulk_update(
                    batch,
                    ['quantity', 'in_stock', 'clothing_sizes'],
                    batch_size=batch_size
                )
                logger.debug(f"Updated {len(batch)} products")

            # Handle variants - first delete old ones for updated products
            if variants_to_create:
                product_ids = [p.id for p in products_to_update if stock_data[p.product_id]['is_clothing']]
                if product_ids:
                    # Delete old variants in batches
                    for i in range(0, len(product_ids), batch_size):
                        batch_ids = product_ids[i:i + batch_size]
                        ProductVariantThrough.objects.filter(product_id__in=batch_ids).delete()
                        ProductVariant.objects.filter(
                            id__in=ProductVariantThrough.objects.filter(
                                product_id__in=batch_ids
                            ).values_list('variant_id', flat=True)
                        ).delete()
                        logger.debug(f"Deleted old variants for {len(batch_ids)} products")

                # Create new variants in batches
                created_variants = []
                for i in range(0, len(variants_to_create), batch_size):
                    batch = variants_to_create[i:i + batch_size]
                    created = ProductVariant.objects.bulk_create(batch)
                    created_variants.extend(created)
                    logger.debug(f"Created {len(created)} variants")

                # Create through relations
                variant_map = {v.sku: v for v in created_variants}
                through_objects = []
                for item in through_to_create:
                    if item['variant_sku'] in variant_map:
                        through_objects.append(
                            ProductVariantThrough(
                                product_id=item['product_id'],
                                variant_id=variant_map[item['variant_sku']].id,
                                quantity=item['quantity'],
                                price=item['price'],
                                old_price=item['old_price']
                            )
                        )

                # Create through relations in batches
                for i in range(0, len(through_objects), batch_size):
                    batch = through_objects[i:i + batch_size]
                    ProductVariantThrough.objects.bulk_create(batch)
                    logger.debug(f"Created {len(batch)} through relations")

    def find_product_by_alt_code(self, code):
        """Find product by alternative code patterns"""
        if not code:
            return None

        # Try to find by partial match (first 6 characters)
        product = XMLProduct.objects.filter(code__startswith(code[:6])).first()
        if product:
            return product

        # Try to find by base code (without size suffix)
        base_code = re.sub(r'[^a-zA-Z0-9]', '', code)
        for size in self.size_mapping.values():
            if base_code.endswith(size):
                base_code = base_code[:-len(size)]
                break

        if base_code and len(base_code) >= 4:
            product = XMLProduct.objects.filter(
                Q(code__startswith(base_code)) |
                Q(code__contains=base_code)
            ).first()



        return product


if __name__ == '__main__':
    Command().handle()