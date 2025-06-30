import os
import requests
import json
from datetime import datetime
from xml.etree import ElementTree as ET
from urllib.parse import urljoin
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.files import File
from io import BytesIO
from bs4 import BeautifulSoup
from main.models import (
    Category, Brand, XMLProduct, SizeChart, SizeVariant
)
from django.conf import settings


class Command(BaseCommand):
    help = 'Import categories and products from gifts.ru XML feed with local image attachments'

    def handle(self, *args, **options):
        # Сначала импортируем категории
        self.import_categories()

        # Затем импортируем товары
        self.import_products()

    def import_categories(self):
        self.stdout.write("Starting categories import...")

        # Удаляем старые категории
        Category.objects.all().delete()

        # Загружаем XML с категориями
        xml_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/catalogue.xml"

        try:
            response = requests.get(xml_url)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            # Сначала создаем все категории без родителей
            for category_elem in root.findall('.//category'):
                if not category_elem.get('parent_id'):
                    self.create_category(category_elem)

            # Затем создаем дочерние категории
            for category_elem in root.findall('.//category'):
                if category_elem.get('parent_id'):
                    self.create_category(category_elem)

            self.stdout.write(self.style.SUCCESS('Successfully imported categories'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing categories: {str(e)}'))

    def create_category(self, category_elem):
        category_id = category_elem.get('id')
        parent_id = category_elem.get('parent_id')
        name = category_elem.find('name').text if category_elem.find('name') is not None else ''

        # Пропускаем категории без имени
        if not name:
            return None

        # Получаем родительскую категорию
        parent = None
        if parent_id:
            try:
                parent = Category.objects.get(xml_id=parent_id)
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Parent category {parent_id} not found for {name}'))
                return None

        # Создаем slug
        slug = slugify(name)
        original_slug = slug
        counter = 1
        while Category.objects.filter(slug=slug).exclude(xml_id=category_id).exists():
            slug = f'{original_slug}-{counter}'
            counter += 1

        # Проверяем существование локального изображения
        image_path = None
        local_image_dir = os.path.join(settings.MEDIA_ROOT, 'categories')
        if os.path.exists(local_image_dir):
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                test_path = os.path.join(local_image_dir, f'{category_id}{ext}')
                if os.path.exists(test_path):
                    image_path = os.path.join('categories', f'{category_id}{ext}')
                    break

        # Создаем или обновляем категорию
        category, created = Category.objects.update_or_create(
            xml_id=category_id,
            defaults={
                'name': name,
                'slug': slug,
                'parent': parent,
                'image': image_path,
                'description': '',
                'is_featured': False,
                'order': 0
            }
        )

        action = "Created" if created else "Updated"
        self.stdout.write(f"{action} category: {name} (ID: {category_id}, Slug: {slug})")

        return category

    def import_products(self):
        self.stdout.write("Starting products import...")

        xml_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/catalogue.xml"

        try:
            response = requests.get(xml_url)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            total_products = len(root.findall('.//product'))
            self.stdout.write(self.style.NOTICE(f'Found {total_products} products in XML feed'))

            imported_count = 0
            skipped_count = 0
            error_count = 0

            for product_elem in root.findall('.//product'):
                try:
                    result = self.process_product(product_elem)
                    if result:
                        imported_count += 1
                        if imported_count % 10 == 0:  # Progress update every 10 products
                            self.stdout.write(
                                self.style.NOTICE(f'Processed {imported_count}/{total_products} products'))
                    else:
                        skipped_count += 1
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'Error processing product: {str(e)}'))
                    continue

            self.stdout.write(self.style.SUCCESS(
                f'Import completed: {imported_count} imported, {skipped_count} skipped, {error_count} errors'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing products: {str(e)}'))

    def process_product(self, product_elem):
        product_id = product_elem.find('product_id').text
        group_id = product_elem.find('group').text if product_elem.find('group') is not None else None

        # Основная информация о товаре
        code = product_elem.find('code').text
        name = product_elem.find('name').text
        description = product_elem.find('content').text if product_elem.find('content') is not None else ''

        # Цены
        price_element = product_elem.find('price/price')
        price = float(price_element.text) if price_element is not None else 0

        old_price_element = product_elem.find('price/oldprice')
        old_price = float(old_price_element.text) if old_price_element is not None else None

        # Наличие
        quantity_element = product_elem.find('quantity')
        quantity = int(quantity_element.text) if quantity_element is not None else 0

        # Бренд
        brand_element = product_elem.find('brand')
        brand_name = brand_element.text if brand_element is not None else ''

        # Статус
        status_element = product_elem.find('status')
        status_id = status_element.get('id') if status_element is not None else '1'
        status_map = {'0': 'new', '1': 'regular', '2': 'limited'}
        status = status_map.get(status_id, 'regular')

        # Дополнительные характеристики
        material = product_elem.find('material').text if product_elem.find('material') is not None else ''
        weight = float(product_elem.find('weight').text) if product_elem.find('weight') is not None else None
        volume = float(product_elem.find('volume').text) if product_elem.find('volume') is not None else None
        barcode = product_elem.find('barcode').text if product_elem.find('barcode') is not None else ''

        # Размеры
        size_type = product_elem.find('size_type').text if product_elem.find('size_type') is not None else ''
        composition = product_elem.find('composition').text if product_elem.find('composition') is not None else ''
        density = product_elem.find('density').text if product_elem.find('density') is not None else ''
        min_order = int(product_elem.find('min_order').text) if product_elem.find('min_order') is not None else 1
        packaging = product_elem.find('packaging').text if product_elem.find('packaging') is not None else ''
        delivery_time = product_elem.find('delivery_time').text if product_elem.find(
            'delivery_time') is not None else ''
        production_time = product_elem.find('production_time').text if product_elem.find(
            'production_time') is not None else ''
        care_instructions = product_elem.find('care_instructions').text if product_elem.find(
            'care_instructions') is not None else ''

        # Обработка изображений - сначала проверяем локальные файлы
        small_image = self.find_local_image(product_id, 'small')
        big_image = self.find_local_image(product_id, 'big')
        super_big_image = self.find_local_image(product_id, 'super_big')

        # Если локальных изображений нет, используем URL из XML
        if not small_image:
            small_image_url = self.get_image_url(product_elem.find('small_image'))
        else:
            small_image_url = ''

        if not big_image:
            big_image_url = self.get_image_url(product_elem.find('big_image'))
        else:
            big_image_url = ''

        if not super_big_image:
            super_big_image_url = self.get_image_url(product_elem.find('super_b_image'))
        else:
            super_big_image_url = ''

        # Дополнительные атрибуты
        attributes = self.get_product_attributes(product_elem)

        # Области нанесения
        print_areas = {}
        for print_item in attributes.get('prints', []):
            print_areas[print_item['code']] = print_item['description']

        # Собираем все данные для XML
        xml_data = {
            'product_id': product_id,
            'group_id': group_id,
            'code': code,
            'name': name,
            'description': description,
            'price': price,
            'old_price': old_price,
            'quantity': quantity,
            'brand': brand_name,
            'status': status,
            'material': material,
            'weight': weight,
            'volume': volume,
            'barcode': barcode,
            'size_type': size_type,
            'composition': composition,
            'density': density,
            'min_order': min_order,
            'packaging': packaging,
            'delivery_time': delivery_time,
            'production_time': production_time,
            'care_instructions': care_instructions,
            'print_areas': print_areas,
            'attributes': attributes,
            'created_at': datetime.now().isoformat()
        }

        # Создаем или обновляем товар
        xml_product, created = XMLProduct.objects.update_or_create(
            product_id=product_id,
            defaults={
                'group_id': group_id,
                'code': code,
                'name': name,
                'description': description,
                'price': price,
                'old_price': old_price,
                'quantity': quantity,
                'small_image': small_image_url,
                'big_image': big_image_url,
                'super_big_image': super_big_image_url,
                'small_image_local': small_image,
                'big_image_local': big_image,
                'super_big_image_local': super_big_image,
                'brand': brand_name,
                'status': status,
                'material': material,
                'weight': weight,
                'volume': volume,
                'barcode': barcode,
                'size_type': size_type,
                'composition': composition,
                'density': density,
                'min_order_quantity': min_order,
                'packaging': packaging,
                'delivery_time': delivery_time,
                'production_time': production_time,
                'care_instructions': care_instructions,
                'print_areas': print_areas,
                'xml_data': xml_data,
                'in_stock': quantity > 0,
                'is_featured': status == 'new',
                'is_bestseller': False
            }
        )

        # Обрабатываем бренд
        if brand_name:
            brand = Brand.objects.filter(name=brand_name).first()
            if not brand:
                base_slug = slugify(brand_name)
                slug = base_slug
                counter = 1
                while Brand.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                brand = Brand.objects.create(name=brand_name, slug=slug)
            xml_product.brand_model = brand

        # Обрабатываем категории
        self.process_categories(product_elem, xml_product)

        # Обрабатываем варианты размеров
        self.process_size_variants(product_elem, xml_product)

        # Обрабатываем таблицы размеров
        self.process_size_charts(xml_product)

        xml_product.save()
        return xml_product

    def find_local_image(self, product_id, size_type):
        """Ищет локальное изображение товара в папке media"""
        media_dir = settings.MEDIA_ROOT
        image_dir = os.path.join(media_dir, 'products', size_type)

        if not os.path.exists(image_dir):
            return None

        # Проверяем различные расширения файлов
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            image_path = os.path.join(image_dir, f'{product_id}{ext}')
            if os.path.exists(image_path):
                return os.path.join('products', size_type, f'{product_id}{ext}')

        return None

    def process_categories(self, product_elem, xml_product):
        # Очищаем существующие категории
        xml_product.categories.clear()

        # Обрабатываем категорию из XML
        category_element = product_elem.find('category')
        if category_element is not None:
            category_name = category_element.text
            category_xml_id = category_element.get('id')

            if category_name and category_xml_id:
                category = Category.objects.filter(xml_id=category_xml_id).first()
                if not category:
                    # Создаем новую категорию, если она не существует
                    slug = slugify(category_name)
                    counter = 1
                    while Category.objects.filter(slug=slug).exists():
                        slug = f"{slugify(category_name)}-{counter}"
                        counter += 1

                    category = Category.objects.create(
                        name=category_name,
                        slug=slug,
                        xml_id=category_xml_id
                    )

                xml_product.categories.add(category)

    def process_size_variants(self, product_elem, xml_product):
        # Очищаем существующие варианты размеров
        SizeVariant.objects.filter(product=xml_product).delete()

        # Обрабатываем варианты из XML
        for variant in product_elem.findall('variants/variant'):
            size = variant.find('size').text if variant.find('size') is not None else ''
            variant_price = float(variant.find('price').text) if variant.find(
                'price') is not None else xml_product.price
            variant_old_price = float(variant.find('oldprice').text) if variant.find(
                'oldprice') is not None else xml_product.old_price
            variant_sku = variant.find('code').text if variant.find('code') is not None else ''
            variant_barcode = variant.find('barcode').text if variant.find('barcode') is not None else ''
            variant_quantity = int(variant.find('quantity').text) if variant.find('quantity') is not None else 0

            SizeVariant.objects.create(
                product=xml_product,
                size=size,
                price=variant_price,
                old_price=variant_old_price,
                sku=variant_sku,
                barcode=variant_barcode,
                quantity=variant_quantity,
                in_stock=variant_quantity > 0
            )

    def process_size_charts(self, xml_product):
        # Очищаем существующие таблицы размеров
        SizeChart.objects.filter(product=xml_product).delete()

        # Извлекаем таблицы размеров из описания
        soup = BeautifulSoup(xml_product.description, 'html.parser')

        for table_div in soup.find_all('div', id='tablemer'):
            img = table_div.find('img')
            table = table_div.find('table')
            note = table_div.find('p')

            if table:
                SizeChart.objects.create(
                    product=xml_product,
                    title=f"Size chart for {xml_product.name}",
                    image_url=img['src'] if img else '',
                    table_html=str(table),
                    note=note.get_text() if note else ''
                )

    def get_image_url(self, image_element):
        if image_element is None:
            return ''

        # Случай 1: Элемент имеет атрибут 'src' (основные изображения)
        if 'src' in image_element.attrib:
            image_path = image_element.attrib['src']
            return f"https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/{image_path}"

        # Случай 2: Элемент имеет текстовое содержимое (вложения)
        if image_element.text and image_element.text.strip():
            image_path = image_element.text.strip()
            return f"https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/{image_path}"

        return ''

    def get_product_attributes(self, product_elem):
        attributes = {}

        # Размер
        if product_elem.find('product_size') is not None:
            attributes['size'] = product_elem.find('product_size').text

        # Фильтры
        filters = []
        for filter_element in product_elem.findall('filters/filter'):
            filter_type = filter_element.find('filtertypeid').text if filter_element.find(
                'filtertypeid') is not None else ''
            filter_id = filter_element.find('filterid').text if filter_element.find('filterid') is not None else ''
            filters.append({'type': filter_type, 'id': filter_id})
        if filters:
            attributes['filters'] = filters

        # Области нанесения
        prints = []
        for print_element in product_elem.findall('print'):
            print_name = print_element.find('name').text if print_element.find('name') is not None else ''
            print_desc = print_element.find('description').text if print_element.find('description') is not None else ''
            prints.append({'code': print_name, 'description': print_desc})
        if prints:
            attributes['prints'] = prints

        # Вложения
        attachments = []
        for attachment in product_elem.findall('product_attachment'):
            attachment_type = 'image' if attachment.find('meaning').text == '1' else 'file'

            # Получаем URL файла
            file_url = ''
            file_element = attachment.find('file')
            if file_element is not None:
                file_url = self.get_image_url(file_element)

            # Получаем URL изображения
            image_url = ''
            image_element = attachment.find('image')
            if image_element is not None:
                image_url = self.get_image_url(image_element)

            name = attachment.find('name').text if attachment.find('name') is not None else ''

            attachments.append({
                'type': attachment_type,
                'file': file_url,
                'image': image_url,
                'name': name
            })

        if attachments:
            attributes['attachments'] = attachments

        return attributes