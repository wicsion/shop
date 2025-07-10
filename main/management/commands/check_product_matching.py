from django.core.management.base import BaseCommand
from main.models import XMLProduct, ProductVariant, ProductVariantThrough
import requests
from xml.etree import ElementTree as ET
from collections import defaultdict
import re


class Command(BaseCommand):
    help = 'Analyze size information and stock quantities with extended analysis'

    def handle(self, *args, **options):
        self.analyze_size_data_in_db()
        self.analyze_size_data_in_xml()

    def analyze_size_data_in_db(self):
        """Анализ информации о размерах в базе данных"""
        self.stdout.write("\n=== Size Analysis in Database ===")

        products_with_sizes = XMLProduct.objects.exclude(sizes_available='').count()
        self.stdout.write(f"Products with sizes defined: {products_with_sizes}")

        variants = ProductVariant.objects.all()
        size_counts = defaultdict(int)

        for variant in variants:
            size_counts[variant.size] += 1

        self.stdout.write("\nSize variants distribution:")
        for size, count in sorted(size_counts.items()):
            self.stdout.write(f"{size}: {count} variants")

        self.stdout.write("\nQuantity by size (through table):")
        through_data = ProductVariantThrough.objects.select_related('variant')
        size_quantities = defaultdict(int)

        for item in through_data:
            size_quantities[item.variant.size] += item.quantity

        for size, quantity in sorted(size_quantities.items()):
            self.stdout.write(f"{size}: {quantity} items in stock")

    def analyze_size_data_in_xml(self):
        """Расширенный анализ информации о размерах в XML"""
        self.stdout.write("\n=== Extended Size Analysis in XML ===")

        session = requests.Session()
        session.auth = ('87358_xmlexport', 'MGzXXSgD')
        xml_url = "https://api2.gifts.ru/export/v2/catalogue/stock.xml"

        try:
            response = session.get(xml_url, timeout=30)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            size_mapping = {
                'XS': 'XS', 'S': 'S', 'M': 'M', 'L': 'L', 'XL': 'XL',
                'XXL': 'XXL', 'XXXL': 'XXXL', '3XL': 'XXXL', '4XL': '4XL', '5XL': '5XL'
            }

            size_patterns = sorted(size_mapping.keys(), key=len, reverse=True)
            size_data = defaultdict(int)
            products_with_sizes = 0
            products_total = 0
            no_size_products = []
            size_variants_in_db = set(ProductVariant.objects.values_list('size', flat=True))

            for item in root.findall('.//stock'):
                products_total += 1
                product_id = item.find('product_id').text.strip() if item.find('product_id') is not None else None
                code = item.find('code').text.strip() if item.find('code') is not None else None
                free = int(item.find('free').text) if item.find('free') is not None else 0

                if not code:
                    continue

                # Определяем размер
                size = None
                code_upper = code.upper()

                # Проверяем конец кода
                for pattern in size_patterns:
                    if code_upper.endswith(pattern):
                        size = size_mapping[pattern]
                        break

                # Проверяем с разделителями
                if not size:
                    for pattern in size_patterns:
                        if f"-{pattern}" in code_upper or f"_{pattern}" in code_upper:
                            size = size_mapping[pattern]
                            break

                if size:
                    products_with_sizes += 1
                    size_data[size] += free
                else:
                    # Анализируем товары без определимого размера
                    no_size_item = {
                        'product_id': product_id,
                        'code': code,
                        'quantity': free,
                        'possible_size': self.guess_possible_size(code),
                        'in_db': self.check_product_in_db(product_id, code)
                    }
                    no_size_products.append(no_size_item)

            self.stdout.write(f"\nTotal products in XML: {products_total}")
            self.stdout.write(
                f"Products with identifiable sizes: {products_with_sizes} ({products_with_sizes / products_total * 100:.1f}%)")
            self.stdout.write(
                f"Products without identifiable sizes: {len(no_size_products)} ({(len(no_size_products) / products_total) * 100:.1f}%)")

            self.stdout.write("\nQuantity by size in XML:")
            for size, quantity in sorted(size_data.items()):
                self.stdout.write(f"{size}: {quantity} items available")

            # Анализ товаров без размеров
            self.stdout.write("\n=== Analysis of products without sizes ===")

            # Новый улучшенный анализ размеров
            self.stdout.write("\nDetailed size patterns in no-size products:")
            size_categories = defaultdict(int)
            detailed_sizes = defaultdict(int)

            for item in no_size_products:
                if item['possible_size']:
                    # Группируем по категориям размеров
                    if 'cm' in item['possible_size'] or 'x' in item['possible_size']:
                        size_categories['Sizes in cm'] += 1
                    elif 'Child' in item['possible_size']:
                        size_categories['Children sizes'] += 1
                    elif 'Shoe' in item['possible_size']:
                        size_categories['Shoe sizes'] += 1
                    elif 'Hat' in item['possible_size']:
                        size_categories['Hat sizes'] += 1
                    elif 'One Size' in item['possible_size']:
                        size_categories['One Size'] += 1
                    else:
                        size_categories['Other sizes'] += 1
                    detailed_sizes[item['possible_size']] += 1

            self.stdout.write("\nSize categories distribution:")
            for category, count in sorted(size_categories.items()):
                self.stdout.write(f"{category}: {count} products")

            self.stdout.write("\nMost common specific sizes (top 20):")
            for size, count in sorted(detailed_sizes.items(), key=lambda x: x[1], reverse=True)[:20]:
                self.stdout.write(f"{size}: {count} products")

            # Проверка наличия в БД
            in_db_count = sum(1 for item in no_size_products if item['in_db'])
            self.stdout.write(f"\nProducts without size but present in DB: {in_db_count}")

            # Примеры товаров без размеров
            self.stdout.write("\nSample of no-size products (max 10):")
            for item in no_size_products[:10]:
                db_status = "Found in DB" if item['in_db'] else "Not in DB"
                self.stdout.write(
                    f"ID: {item['product_id']}, Code: {item['code']}, Possible size: {item['possible_size']}, {db_status}")

            # Сохраняем полный список для анализа
            with open('no_size_products.csv', 'w') as f:
                f.write("product_id,code,quantity,possible_size,in_db\n")
                for item in no_size_products:
                    f.write(
                        f"{item['product_id']},{item['code']},{item['quantity']},{item['possible_size']},{item['in_db']}\n")
            self.stdout.write("\nSaved full list to no_size_products.csv")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error analyzing XML: {str(e)}"))

    def guess_possible_size(self, code):
        """Улучшенное определение размеров, включая сантиметры и составные размеры"""
        if not code:
            return None

        code_upper = code.upper()

        # 1. Стандартные размеры (XS, S, M, L, XL и т.д.)
        size_mapping = {
            'XS': 'XS', 'S': 'S', 'M': 'M', 'L': 'L', 'XL': 'XL',
            'XXL': 'XXL', 'XXXL': 'XXXL', '3XL': 'XXXL', '4XL': '4XL', '5XL': '5XL'
        }

        for pattern, size in size_mapping.items():
            if (code_upper.endswith(pattern) or
                    f"-{pattern}" in code_upper or
                    f"_{pattern}" in code_upper):
                return size

        # 2. Размеры в сантиметрах
        cm_patterns = [
            (r'(\d{2,3})[XХ×](\d{2,3})', 'Size {0}x{1} cm'),
            (r'(\d{2,3})\s*[-/]\s*(\d{2,3})', 'Size {0}-{1} cm'),
            (r'(\d{2,3})\s*[ШШW]\s*(\d{2,3})', 'Size {0}W{1}'),
        ]

        for pattern, format_str in cm_patterns:
            match = re.search(pattern, code_upper)
            if match:
                try:
                    size1 = int(match.group(1))
                    size2 = int(match.group(2))
                    if 20 <= size1 <= 200 and 20 <= size2 <= 200:
                        return format_str.format(size1, size2)
                except (ValueError, IndexError):
                    continue

        # 3. Одиночные размеры в см
        single_size_match = re.search(r'(\d{2,3})(?:\D|$)', code_upper)
        if single_size_match:
            try:
                size = int(single_size_match.group(1))
                if 20 <= size <= 200:
                    return f"Size {size} cm"
            except ValueError:
                pass

        # 4. Детские размеры
        child_size_match = re.search(r'(\d{2,3})\s*[-/]\s*(\d{2,3})', code_upper)
        if child_size_match:
            try:
                size1 = int(child_size_match.group(1))
                size2 = int(child_size_match.group(2))
                if 50 <= size1 <= 170 and 50 <= size2 <= 170:
                    return f"Child size {size1}-{size2} cm"
            except (ValueError, IndexError):
                pass

        child_t_match = re.search(r'(\d)T', code_upper)
        if child_t_match:
            return f"Child size {child_t_match.group(1)}T"

        # 5. Буквенные обозначения
        other_sizes = {
            'ONE': 'One Size',
            'OS': 'One Size',
            'UNI': 'Universal',
            'MULTI': 'Multisize',
            'FREE': 'Free Size',
            'REG': 'Regular',
            'PET': 'Petite',
            'TALL': 'Tall'
        }

        for pattern, size_name in other_sizes.items():
            if pattern in code_upper:
                return size_name

        # 6. Размеры обуви
        shoe_size_match = re.search(r'\b(\d{2})\b', code_upper)
        if shoe_size_match:
            try:
                size = int(shoe_size_match.group(1))
                if 35 <= size <= 50:
                    return f"Shoe size {size}"
            except ValueError:
                pass

        # 7. Размеры головных уборов
        hat_size_match = re.search(r'\b(\d{2})\b', code_upper)
        if hat_size_match:
            try:
                size = int(hat_size_match.group(1))
                if 50 <= size <= 65:
                    return f"Hat size {size}"
            except ValueError:
                pass

        return None

    def check_product_in_db(self, product_id, code):
        """Проверяем, есть ли товар в базе данных"""
        return (XMLProduct.objects.filter(product_id=product_id).exists() or
                XMLProduct.objects.filter(code=code).exists())