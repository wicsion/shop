import requests
from xml.etree import ElementTree as ET
from django.core.files import File
from io import BytesIO
from main.models import Category, Brand, XMLProduct
import os
from urllib.parse import urlparse
from django.db import transaction


class GiftsXMLImporter:
    def __init__(self, login, password):
        self.base_url = "https://api2.gifts.ru/export/v2/catalogue"
        self.auth = (login, password)
        self.session = requests.Session()
        self.session.auth = self.auth

    def register_ip(self, ip, site_url):
        url = f"https://{self.auth[0]}:{self.auth[1]}@api2.gifts.ru/export/v2/registerip/{ip}/{site_url}"
        response = requests.post(url)
        return response.status_code == 200

    def download_xml(self, xml_type='catalogue'):
        url = f"{self.base_url}/{xml_type}.xml"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.content
        return None

    def download_file(self, url):
        try:
            response = self.session.get(url, stream=True)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print(f"Error downloading file {url}: {str(e)}")
        return None

    @transaction.atomic
    def import_categories(self, xml_content):
        root = ET.fromstring(xml_content)
        categories = {}

        # First pass - create all categories
        for category in root.findall('.//category'):
            xml_id = category.get('id')
            name = category.find('name').text
            parent_id = category.get('parentId')

            if xml_id not in categories:
                categories[xml_id] = {
                    'name': name,
                    'parent_id': parent_id,
                    'object': None
                }

        # Second pass - create hierarchy
        for xml_id, data in categories.items():
            parent = None
            if data['parent_id'] in categories:
                parent = categories[data['parent_id']]['object']

            category, created = Category.objects.get_or_create(
                xml_id=xml_id,
                defaults={
                    'name': data['name'],
                    'parent': parent
                }
            )

            if not created:
                category.name = data['name']
                category.parent = parent
                category.save()

            categories[xml_id]['object'] = category

        return categories

    @transaction.atomic
    def import_brands(self, xml_content):
        root = ET.fromstring(xml_content)
        brands = {}

        for brand in root.findall('.//brand'):
            name = brand.find('name').text
            if name and name not in brands:
                brand_obj, created = Brand.objects.get_or_create(
                    name=name,
                    defaults={'is_active': True}
                )
                brands[name] = brand_obj

        return brands

    @transaction.atomic
    def import_products(self, xml_content, categories, brands):
        root = ET.fromstring(xml_content)

        for product in root.findall('.//product'):
            product_id = product.get('id')
            name = product.find('name').text
            description = product.find('description').text if product.find('description') is not None else ''
            price = float(product.find('price').text)
            old_price = float(product.find('oldprice').text) if product.find('oldprice') is not None else None
            brand_name = product.find('brand').text if product.find('brand') is not None else None
            in_stock = product.find('instock').text.lower() == 'true' if product.find('instock') is not None else False
            quantity = int(product.find('quantity').text) if product.find('quantity') is not None else 0

            # Get images
            small_image = product.find('smallImage').text if product.find('smallImage') is not None else None
            big_image = product.find('bigImage').text if product.find('bigImage') is not None else None

            # Get categories
            product_categories = []
            for cat in product.findall('.//categoryId'):
                cat_id = cat.text
                if cat_id in categories:
                    product_categories.append(categories[cat_id]['object'])

            # Create or update product
            product_obj, created = XMLProduct.objects.get_or_create(
                product_id=product_id,
                defaults={
                    'name': name,
                    'description': description,
                    'price': price,
                    'old_price': old_price,
                    'brand': brand_name,
                    'in_stock': in_stock,
                    'quantity': quantity,
                    'small_image': small_image,
                    'big_image': big_image,
                }
            )

            if not created:
                product_obj.name = name
                product_obj.description = description
                product_obj.price = price
                product_obj.old_price = old_price
                product_obj.brand = brand_name
                product_obj.in_stock = in_stock
                product_obj.quantity = quantity
                product_obj.small_image = small_image
                product_obj.big_image = big_image
                product_obj.save()

            # Set categories
            product_obj.categories.set(product_categories)

            # Set brand model if exists
            if brand_name and brand_name in brands:
                product_obj.brand_model = brands[brand_name]
                product_obj.save()

            # Download images if needed
            if created or not product_obj.small_image_local:
                self.download_product_images(product_obj)

    def download_product_images(self, product):
        if product.small_image:
            content = self.download_file(product.small_image)
            if content:
                img_name = os.path.basename(urlparse(product.small_image).path)
                product.small_image_local.save(img_name, BytesIO(content), save=True)

        if product.big_image:
            content = self.download_file(product.big_image)
            if content:
                img_name = os.path.basename(urlparse(product.big_image).path)
                product.big_image_local.save(img_name, BytesIO(content), save=True)

    def full_import(self, site_url, ip_address=None):
        # Register IP if needed
        if ip_address:
            self.register_ip(ip_address, site_url)

        # Download and parse catalogue.xml
        xml_content = self.download_xml('catalogue')
        if not xml_content:
            return False

        # Import data
        categories = self.import_categories(xml_content)
        brands = self.import_brands(xml_content)
        self.import_products(xml_content, categories, brands)

        return True