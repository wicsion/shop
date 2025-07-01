from xml.etree import ElementTree as ET
from django.core.management.base import BaseCommand
from main.models import XMLProduct, Category, Brand
from urllib.parse import urljoin
from django.utils.text import slugify, get_valid_filename
from datetime import datetime
import re
from bs4 import BeautifulSoup
import logging
import time
from tqdm import tqdm
import os
from PIL import Image
import requests
from io import BytesIO
from django.db import connection

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('import_debug.log'),
        logging.StreamHandler()
    ]
)


def clean_filename(filename):
    """Очищает имя файла от недопустимых символов"""
    filename = get_valid_filename(filename)
    filename = re.sub(r'^[A-Za-z]:[\\/]', '', filename)  # Удаляем компоненты пути Windows
    return filename[:100]  # Ограничиваем длину имени


class Command(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.session.auth = ('87358_xmlexport', 'MGzXXSgD')
        self.processed_images_urls = set()
        self.download_missing = False
        self.total_products = 0
        self.total_images = 0
        self.processed_images_count = 0
        self.start_time = None

    def add_arguments(self, parser):
        parser.add_argument('--offset', type=int, default=0, help='Смещение для начала импорта')
        parser.add_argument('--limit', type=int, default=None, help='Лимит импортируемых товаров')
        parser.add_argument('--no-input', action='store_true', help='Не запрашивать подтверждение')
        parser.add_argument('--delay', type=float, default=0.1, help='Задержка между обработкой товаров (секунды)')
        parser.add_argument('--download-missing', action='store_true', help='Загружать отсутствующие изображения')
        parser.add_argument('--force-update', action='store_true', help='Обновлять существующие товары')
        parser.add_argument('--batch-size', type=int, default=100, help='Количество товаров для пакетной обработки')

    def handle(self, *args, **options):
        self.start_time = time.time()
        self.download_missing = options['download_missing']

        xml_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/product.xml"

        try:
            headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'}

            for attempt in range(3):
                try:
                    response = requests.get(xml_url, headers=headers, timeout=30)
                    response.raise_for_status()
                    break
                except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                    if attempt == 2:
                        raise
                    time.sleep(5 * (attempt + 1))

            root = ET.fromstring(response.content)
            products = list(root.findall('product'))
            products = products[options['offset']:options['offset'] + options['limit']] if options[
                'limit'] else products[options['offset']:]

            self.total_products = len(products)
            self.total_images = sum(
                len(p.findall('product_attachment')) +
                (1 if p.find('big_image') is not None else 0) +
                (1 if p.find('small_image') is not None else 0)
                for p in products
            )

            logger.info(f"Начало обработки: {self.total_products} товаров, {self.total_images} изображений")

            if options['batch_size'] > 1:
                self.process_product_batch(products, options)
            else:
                self.process_products_sequentially(products, options)

            self.stdout.write(self.style.SUCCESS(f"Успешно: {len(products)} товаров"))

        except Exception as e:
            logger.critical(f"Фатальная ошибка: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f"Ошибка импорта: {str(e)}"))
            if not options['no_input']:
                raise

        finally:
            connection.close()
            if 'response' in locals():
                response.close()

            total_time = time.time() - self.start_time
            logger.info(
                f"Импорт завершен: {self.total_products} товаров, {self.total_images} изображений\n"
                f"Общее время: {total_time / 60:.1f} минут\n"
                f"Средняя скорость: {self.total_images / total_time:.1f} фото/сек"
            )

    def process_products_sequentially(self, products, options):
        """Обработка товаров последовательно"""
        for product in products:
            try:
                product_id = product.find('product_id').text.strip()
                if XMLProduct.objects.filter(product_id=product_id).exists() and not options.get('force_update'):
                    continue

                self.process_product(product, options)

                if options['delay'] > 0:
                    time.sleep(options['delay'])

            except Exception as e:
                logger.error(f"Ошибка товара {product_id}: {str(e)}", exc_info=True)
                if not options.get('no_input'):
                    self.stdout.write(self.style.ERROR(f"Ошибка товара {product_id}: {str(e)}"))

    def process_product_batch(self, products, options):
        with tqdm(total=len(products), desc=f"Импорт партиями по {options['batch_size']}") as pbar:
            for i in range(0, len(products), options['batch_size']):
                batch = products[i:i + options['batch_size']]

                for product in batch:
                    try:
                        product_id = product.find('product_id').text.strip()
                        pbar.set_postfix({'id': product_id})

                        if not options.get('force_update'):
                            if XMLProduct.objects.filter(product_id=product_id).exists():
                                continue

                        self.process_product(product, options)
                        pbar.update(1)

                    except Exception as e:
                        logger.error(f"Ошибка товара {product_id}: {str(e)}", exc_info=True)
                        if not options.get('no_input'):
                            self.stdout.write(self.style.ERROR(f"Ошибка товара {product_id}: {str(e)}"))

    def get_image_url(self, image_element):
        """Извлекает URL изображения из XML элемента без изменения размера"""
        if image_element is None:
            return ''

        image_path = (
                image_element.get('src', '').strip()
                or image_element.text.strip()
                or ''
        )

        if not image_path:
            return ''

        base_url = "https://api2.gifts.ru/export/v2/catalogue/"
        full_url = urljoin(base_url, image_path)
        return full_url

    def convert_url_to_local_path(self, image_url, is_attachment=False):
        """Генерирует локальный путь с нормализованным именем файла"""
        if not image_url:
            return ''

        filename = image_url.split('/')[-1].split('?')[0]
        filename = filename.split('.')[0]
        filename = clean_filename(filename)
        filename = f"{filename}.webp"

        if is_attachment:
            path = os.path.join('attachments', filename)
        else:
            path = os.path.join('products', 'main', filename)

        return path

    def process_product(self, product, options):
        """Обрабатывает один товар из XML"""
        try:
            # Основная информация
            product_id = product.find('product_id').text.strip()
            code = product.find('code').text.strip() if product.find('code') is not None else ''
            name = product.find('name').text.strip() if product.find('name') is not None else ''
            description = product.find('content').text.strip() if product.find('content') is not None else ''

            # Флаги
            made_in_russia = self.get_bool_value(product, 'made_in_russia')
            is_eco = self.get_bool_value(product, 'is_eco')
            for_kids = self.get_bool_value(product, 'for_kids')
            is_profitable = self.get_bool_value(product, 'is_profitable')

            # Технические характеристики
            application_type = self.get_text_value(product, 'application_type')
            mechanism_type = self.get_text_value(product, 'mechanism_type')
            ball_diameter = self.get_text_value(product, 'ball_diameter')
            refill_type = self.get_text_value(product, 'refill_type')
            replaceable_refill = self.get_bool_value(product, 'replaceable_refill')
            format_size = self.get_text_value(product, 'format_size')
            cover_type = self.get_text_value(product, 'cover_type')
            block_color = self.get_text_value(product, 'block_color')
            edge_type = self.get_text_value(product, 'edge_type')
            page_count = self.get_int_value(product, 'page_count')
            calendar_grid = self.get_text_value(product, 'calendar_grid')
            ribbon_color = self.get_text_value(product, 'ribbon_color')
            box_size = self.get_text_value(product, 'box_size')
            density = self.get_text_value(product, 'density')
            expiration_date = self.get_text_value(product, 'expiration_date')

            # Дополнительные атрибуты
            pantone_color = self.get_text_value(product, 'pantone_color')
            gender = self.get_text_value(product, 'gender')
            requires_marking = self.get_bool_value(product, 'requires_marking')
            individual_packaging = self.get_bool_value(product, 'individual_packaging')
            cover_material = self.get_text_value(product, 'cover_material')
            block_number = self.get_text_value(product, 'block_number')
            collection = self.get_text_value(product, 'collection')
            dating = self.get_text_value(product, 'dating')

            # Новые поля для одежды и аксессуаров
            sizes_available = self.get_text_value(product, 'sizes_available')
            dimensions = self.get_text_value(product, 'dimensions')
            fit = self.get_text_value(product, 'fit')
            cut = self.get_text_value(product, 'cut')
            lining = self.get_text_value(product, 'lining')
            has_lining = self.get_bool_value(product, 'has_lining')
            video_link = self.get_text_value(product, 'video_link')
            stock_marking = self.get_text_value(product, 'stock_marking')
            umbrella_type = self.get_text_value(product, 'umbrella_type')
            marking_type = self.get_text_value(product, 'marking_type')
            packaging_type = self.get_text_value(product, 'packaging_type')

            # Цены
            price = self.get_float_value(product, 'price/price')
            old_price = self.get_float_value(product, 'price/oldprice')

            # Бренд и статус
            brand_name = self.get_text_value(product, 'brand')
            status = self.get_product_status(product)

            # Дополнительные параметры
            material = self.get_text_value(product, 'material')
            weight = self.get_float_value(product, 'weight')
            volume = self.get_float_value(product, 'volume')
            barcode = self.get_text_value(product, 'barcode')

            # Альтернативные ID
            alt_ids = self.get_alt_ids(product_id, code)

            # Обработка изображений
            main_image_url, additional_image_urls = self.process_product_images(product)
            image_count = len(additional_image_urls) + (1 if main_image_url else 0)
            self.processed_images_count += image_count

            # Формируем данные товара
            xml_data = {
                'product_id': product_id,
                'code': code,
                'name': name,
                'description': description,
                'price': price,
                'old_price': old_price,
                'brand': brand_name,
                'status': status,
                'material': material,
                'weight': weight,
                'volume': volume,
                'barcode': barcode,
                'main_image_url': main_image_url,
                'additional_image_urls': additional_image_urls,
                'attributes': self.get_product_attributes(product),
                'created_at': datetime.now().isoformat(),
                'made_in_russia': made_in_russia,
                'is_eco': is_eco,
                'for_kids': for_kids,
                'is_profitable': is_profitable,
                'application_type': application_type,
                'mechanism_type': mechanism_type,
                'ball_diameter': ball_diameter,
                'refill_type': refill_type,
                'replaceable_refill': replaceable_refill,
                'format_size': format_size,
                'cover_type': cover_type,
                'block_color': block_color,
                'edge_type': edge_type,
                'page_count': page_count,
                'calendar_grid': calendar_grid,
                'ribbon_color': ribbon_color,
                'box_size': box_size,
                'density': density,
                'expiration_date': expiration_date,
                'pantone_color': pantone_color,
                'gender': gender,
                'requires_marking': requires_marking,
                'individual_packaging': individual_packaging,
                'cover_material': cover_material,
                'block_number': block_number,
                'collection': collection,
                'dating': dating,
                'sizes_available': sizes_available,
                'dimensions': dimensions,
                'fit': fit,
                'cut': cut,
                'lining': lining,
                'has_lining': has_lining,
                'video_link': video_link,
                'stock_marking': stock_marking,
                'umbrella_type': umbrella_type,
                'marking_type': marking_type,
                'packaging_type': packaging_type
            }

            # Создание/обновление товара
            defaults = {
                'code': code,
                'name': name,
                'description': description,
                'price': price,
                'old_price': old_price,
                'status': status,
                'material': material,
                'weight': weight,
                'volume': volume,
                'barcode': barcode,
                'xml_data': xml_data,
                'alt_ids': alt_ids,
                'in_stock': True,
                'is_featured': status == 'new',
                'is_bestseller': False,
                'was_imported': True,
                'made_in_russia': made_in_russia,
                'is_eco': is_eco,
                'for_kids': for_kids,
                'is_profitable': is_profitable,
                'application_type': application_type,
                'mechanism_type': mechanism_type,
                'ball_diameter': ball_diameter,
                'refill_type': refill_type,
                'replaceable_refill': replaceable_refill,
                'format_size': format_size,
                'cover_type': cover_type,
                'block_color': block_color,
                'edge_type': edge_type,
                'page_count': page_count,
                'calendar_grid': calendar_grid,
                'ribbon_color': ribbon_color,
                'box_size': box_size,
                'density': density,
                'expiration_date': expiration_date,
                'pantone_color': pantone_color,
                'gender': gender,
                'requires_marking': requires_marking,
                'individual_packaging': individual_packaging,
                'cover_material': cover_material,
                'block_number': block_number,
                'collection': collection,
                'dating': dating,
                'sizes_available': sizes_available,
                'dimensions': dimensions,
                'fit': fit,
                'cut': cut,
                'lining': lining,
                'has_lining': has_lining,
                'video_link': video_link,
                'stock_marking': stock_marking,
                'umbrella_type': umbrella_type,
                'marking_type': marking_type,
                'packaging_type': packaging_type,
                'special_filters': xml_data.get('attributes', {}).get('filters', [])
            }

            xml_product, created = XMLProduct.objects.update_or_create(
                product_id=product_id,
                defaults=defaults
            )

            # Обработка бренда
            if brand_name:
                self.process_brand(brand_name, xml_product)

            # Привязка к категории
            self.process_category(product, xml_product)

            action = "Создан" if created else "Обновлен"
            self.stdout.write(self.style.SUCCESS(f"{action} товар: {product_id}"))

            self.log_progress()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка обработки товара: {str(e)}"))
            logger.exception(f"Ошибка товара {product_id if 'product_id' in locals() else 'UNKNOWN'}: {str(e)}")

    def get_text_value(self, product, element_name):
        """Получает текстовое значение из XML элемента"""
        element = product.find(element_name)
        return element.text.strip() if element is not None and element.text is not None else ''

    def get_bool_value(self, product, element_name):
        """Получает булево значение из XML элемента"""
        element = product.find(element_name)
        return element is not None and element.text.lower() == 'true'

    def get_int_value(self, product, element_name):
        """Получает целочисленное значение из XML элемента"""
        element = product.find(element_name)
        if element is not None and element.text.strip():
            try:
                return int(element.text)
            except ValueError:
                return None
        return None

    def get_float_value(self, product, element_name):
        """Получает числовое значение с плавающей точкой из XML элемента"""
        element = product.find(element_name)
        if element is not None and element.text.strip():
            try:
                return float(element.text)
            except ValueError:
                return None
        return None

    def get_product_status(self, product):
        """Определяет статус товара"""
        status_element = product.find('status')
        status_id = status_element.get('id') if status_element is not None else '1'
        status_map = {'0': 'new', '1': 'regular', '2': 'limited'}
        return status_map.get(status_id, 'regular')

    def get_alt_ids(self, product_id, code):
        """Генерирует альтернативные ID товара"""
        alt_ids = []
        if code:
            alt_ids.append(code)
        if product_id != product_id.lstrip('0'):
            alt_ids.append(product_id.lstrip('0'))
        return alt_ids

    def process_product_images(self, product):
        """Обрабатывает изображения товара"""
        main_image_url = ''
        additional_image_urls = []

        # Обработка вложений (attachments)
        attachments = product.findall('product_attachment')
        for attachment in attachments:
            if attachment.find('meaning') is not None and attachment.find('meaning').text == '1':
                image_element = attachment.find('image')
                if image_element is not None:
                    image_url = self.get_image_url(image_element)
                    if image_url:
                        if not main_image_url:
                            main_image_url = image_url
                        else:
                            additional_image_urls.append(image_url)

        # Если основное изображение не найдено в attachments, проверяем стандартные поля
        if not main_image_url:
            main_image_element = product.find('big_image') or product.find('small_image')
            if main_image_element is not None:
                main_image_url = self.get_image_url(main_image_element)

        return main_image_url, additional_image_urls

    def process_brand(self, brand_name, xml_product):
        """Обрабатывает бренд товара"""
        try:
            base_slug = slugify(brand_name)
            slug = base_slug
            counter = 1

            while Brand.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            brand, brand_created = Brand.objects.get_or_create(
                name=brand_name,
                defaults={
                    'slug': slug,
                    'is_active': True
                }
            )

            if brand_created:
                self.stdout.write(self.style.SUCCESS(f"Создан бренд: {brand_name}"))

            xml_product.brand = brand.name
            xml_product.brand_link = brand
            xml_product.save()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка обработки бренда: {str(e)}"))

    def process_category(self, product, xml_product):
        """Обрабатывает категорию товара"""
        page_id = product.find('page').text if product.find('page') is not None else None
        if page_id:
            try:
                category = Category.objects.get(xml_id=page_id)
                xml_product.categories.add(category)
            except Category.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Категория не найдена: {page_id}"))

    def log_progress(self):
        """Логирует прогресс обработки"""
        elapsed = time.time() - self.start_time
        processed = self.processed_images_count
        remaining = (elapsed / processed) * (self.total_images - processed) if processed > 0 else 0

        logger.info(
            f"Прогресс: {processed}/{self.total_images} фото "
            f"({processed / self.total_images:.1%}) | "
            f"Осталось: {remaining / 60:.1f} мин | "
            f"Скорость: {processed / elapsed:.1f} фото/сек"
        )

    def get_product_attributes(self, product):
        """Извлекает дополнительные атрибуты из XML"""
        attributes = {
            # Основные атрибуты
            'size': self.get_text_value(product, 'product_size'),

            # Флаги
            'made_in_russia': self.get_bool_value(product, 'made_in_russia'),
            'is_eco': self.get_bool_value(product, 'is_eco'),
            'for_kids': self.get_bool_value(product, 'for_kids'),
            'is_profitable': self.get_bool_value(product, 'is_profitable'),

            # Технические характеристики
            'application_type': self.get_text_value(product, 'application_type'),
            'mechanism_type': self.get_text_value(product, 'mechanism_type'),
            'ball_diameter': self.get_text_value(product, 'ball_diameter'),
            'refill_type': self.get_text_value(product, 'refill_type'),
            'replaceable_refill': self.get_bool_value(product, 'replaceable_refill'),
            'format_size': self.get_text_value(product, 'format_size'),
            'cover_type': self.get_text_value(product, 'cover_type'),
            'block_color': self.get_text_value(product, 'block_color'),
            'edge_type': self.get_text_value(product, 'edge_type'),
            'page_count': self.get_int_value(product, 'page_count'),
            'calendar_grid': self.get_text_value(product, 'calendar_grid'),
            'ribbon_color': self.get_text_value(product, 'ribbon_color'),
            'box_size': self.get_text_value(product, 'box_size'),
            'density': self.get_text_value(product, 'density'),
            'expiration_date': self.get_text_value(product, 'expiration_date'),

            # Дополнительные атрибуты
            'pantone_color': self.get_text_value(product, 'pantone_color'),
            'gender': self.get_text_value(product, 'gender'),
            'requires_marking': self.get_bool_value(product, 'requires_marking'),
            'individual_packaging': self.get_bool_value(product, 'individual_packaging'),
            'cover_material': self.get_text_value(product, 'cover_material'),
            'block_number': self.get_text_value(product, 'block_number'),
            'collection': self.get_text_value(product, 'collection'),
            'dating': self.get_text_value(product, 'dating'),

            # Новые поля
            'sizes_available': self.get_text_value(product, 'sizes_available'),
            'dimensions': self.get_text_value(product, 'dimensions'),
            'fit': self.get_text_value(product, 'fit'),
            'cut': self.get_text_value(product, 'cut'),
            'lining': self.get_text_value(product, 'lining'),
            'has_lining': self.get_bool_value(product, 'has_lining'),
            'video_link': self.get_text_value(product, 'video_link'),
            'stock_marking': self.get_text_value(product, 'stock_marking'),
            'umbrella_type': self.get_text_value(product, 'umbrella_type'),
            'marking_type': self.get_text_value(product, 'marking_type'),
            'packaging_type': self.get_text_value(product, 'packaging_type'),

            # Фильтры и принты
            'filters': [
                {'type': f.find('filtertypeid').text, 'id': f.find('filterid').text}
                for f in product.findall('filters/filter')
                if f.find('filtertypeid') is not None and f.find('filterid') is not None
            ],
            'prints': [
                {'code': p.find('name').text, 'description': p.find('description').text}
                for p in product.findall('print')
                if p.find('name') is not None
            ],

            # Вложения
            'attachments': [
                {
                    'type': 'image' if a.find('meaning') is not None and a.find('meaning').text == '1' else 'file',
                    'file': self.get_image_url(a.find('file')) if a.find('file') is not None else '',
                    'image': self.get_image_url(a.find('image')) if a.find('image') is not None else '',
                    'name': a.find('name').text if a.find('name') is not None else '',
                    'meaning': a.find('meaning').text if a.find('meaning') is not None else '0'
                }
                for a in product.findall('product_attachment')
            ]
        }

        # Парсинг таблицы размеров
        if product.find('content') is not None:
            size_table = self.parse_size_table(product.find('content').text)
            if size_table:
                attributes['size_table'] = size_table

        return attributes

    def parse_size_table(self, description):
        """Парсит таблицу размеров из описания"""
        if not description:
            return None

        try:
            soup = BeautifulSoup(description, 'html.parser')
            if not (table := soup.find('table')):
                return None

            headers = []
            if header_row := table.find('tr'):
                headers = [th.get_text(strip=True) for th in header_row.find_all('td')]

            rows = []
            for row in table.find_all('tr')[1:]:
                if row_data := [cell.get_text(strip=True) for cell in row.find_all('td')]:
                    rows.append(row_data)

            return {'headers': headers, 'rows': rows}

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Ошибка парсинга размеров: {str(e)}"))
            return None