import requests
from xml.etree import ElementTree as ET
from django.core.management.base import BaseCommand
from main.models import XMLProduct, Category, Brand
from urllib.parse import urljoin
from django.utils.text import slugify
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Import products from XML feed for Project 111'

    def handle(self, *args, **options):
        xml_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/product.xml"

        try:
            response = requests.get(xml_url)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            for product in root.findall('product'):
                self.process_product(product)

            self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(root.findall("product"))} products'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing products: {str(e)}'))

    def process_product(self, product):
        product_id = product.find('product_id').text
        group_id = product.find('group').text if product.find('group') is not None else None

        # Basic product info
        code = product.find('code').text
        name = product.find('name').text
        description = product.find('content').text if product.find('content') is not None else ''

        # Price handling
        price_element = product.find('price/price')
        price = float(price_element.text) if price_element is not None else 0

        # Images
        small_image = self.get_image_url(product.find('small_image'))
        big_image = self.get_image_url(product.find('big_image'))
        super_big_image = self.get_image_url(product.find('super_big_image'))

        # Brand handling
        brand_element = product.find('brand')
        brand_name = brand_element.text if brand_element is not None else ''

        # Status
        status_element = product.find('status')
        status_id = status_element.get('id') if status_element is not None else '1'
        status_map = {'0': 'new', '1': 'regular', '2': 'limited'}
        status = status_map.get(status_id, 'regular')

        # Additional fields
        material = product.find('material').text if product.find('material') is not None else ''
        weight = float(product.find('weight').text) if product.find('weight') is not None else None
        volume = float(product.find('volume').text) if product.find('volume') is not None else None
        barcode = product.find('barcode').text if product.find('barcode') is not None else ''

        # XML data for all product info
        xml_data = {
            'product_id': product_id,
            'group_id': group_id,
            'code': code,
            'name': name,
            'description': description,
            'price': price,
            'images': {
                'small': small_image,
                'big': big_image,
                'super_big': super_big_image
            },
            'brand': brand_name,
            'status': status,
            'material': material,
            'weight': weight,
            'volume': volume,
            'barcode': barcode,
            'attributes': self.get_product_attributes(product),
            'created_at': datetime.now().isoformat()
        }

        # Create or update product
        xml_product, created = XMLProduct.objects.update_or_create(
            product_id=product_id,
            defaults={
                'group_id': group_id,
                'code': code,
                'name': name,
                'description': description,
                'price': price,
                'small_image': small_image,
                'big_image': big_image,
                'super_big_image': super_big_image,
                'brand': brand_name,
                'status': status,
                'material': material,
                'weight': weight,
                'volume': volume,
                'barcode': barcode,
                'xml_data': xml_data,
                'in_stock': True,  # Will be updated by stock import
                'is_featured': status == 'new',
                'is_bestseller': False  # Can be set manually or by logic
            }
        )

        # Handle brand relationship
        if brand_name:
            # Сначала пытаемся найти бренд по имени
            brand = Brand.objects.filter(name=brand_name).first()

            if not brand:
                # Если бренда нет, создаем новый с уникальным slug
                base_slug = slugify(brand_name)
                slug = base_slug
                counter = 1

                # Проверяем уникальность slug
                while Brand.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                brand = Brand.objects.create(
                    name=brand_name,
                    slug=slug
                )

            xml_product.brand_model = brand
            xml_product.save()

        return xml_product

    def get_image_url(self, image_element):
        if image_element is not None and 'src' in image_element.attrib:
            base_url = "https://api2.gifts.ru/export/v2/catalogue/"
            return urljoin(base_url, image_element.attrib['src'])
        return ''

    def get_product_attributes(self, product):
        attributes = {}

        # Size
        if product.find('product_size') is not None:
            attributes['size'] = product.find('product_size').text

        # Filters
        filters = []
        for filter_element in product.findall('filters/filter'):
            filter_type = filter_element.find('filtertypeid').text if filter_element.find(
                'filtertypeid') is not None else ''
            filter_id = filter_element.find('filterid').text if filter_element.find('filterid') is not None else ''
            filters.append({'type': filter_type, 'id': filter_id})
        if filters:
            attributes['filters'] = filters

        # Prints
        prints = []
        for print_element in product.findall('print'):
            print_name = print_element.find('name').text if print_element.find('name') is not None else ''
            print_desc = print_element.find('description').text if print_element.find('description') is not None else ''
            prints.append({'code': print_name, 'description': print_desc})
        if prints:
            attributes['prints'] = prints

        # Attachments
        attachments = []
        for attachment in product.findall('product_attachment'):
            attachment_type = 'image' if attachment.find('meaning').text == '1' else 'file'
            file_url = self.get_image_url(attachment.find('file')) if attachment.find('file') is not None else ''
            image_url = self.get_image_url(attachment.find('image')) if attachment.find('image') is not None else ''
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