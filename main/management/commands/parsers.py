import requests
from xml.etree import ElementTree as ET
from django.core.files import File
from io import BytesIO
from main.models import Category, Brand, XMLProduct, SizeVariant, SizeChart
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Данные авторизации
AUTH = ('87358_xmlexport', 'MGzXXSgD')
BASE_URL = 'https://api2.gifts.ru/export/v2/catalogue/'


def parse_xml_files():
    """
    Основная функция для парсинга всех XML-файлов
    """
    # 1. Парсим структуру каталога (tree.xml)
    categories = parse_tree_xml()

    # 2. Парсим товары (product.xml)
    parse_product_xml(categories)

    # 3. Парсим наличие товаров (stock.xml) - опционально
    parse_stock_xml()


def parse_tree_xml():
    """
    Парсим файл tree.xml для получения структуры категорий
    """
    url = urljoin(BASE_URL, 'tree.xml')
    response = requests.get(url, auth=AUTH)
    root = ET.fromstring(response.content)

    categories = {}

    # Сначала создаем все категории без связей
    for category_elem in root.findall('category'):
        xml_id = category_elem.get('id')
        name = category_elem.find('name').text
        parent_id = category_elem.get('parentId')

        # Создаем или получаем категорию
        category, created = Category.objects.get_or_create(
            xml_id=xml_id,
            defaults={
                'name': name,
                'slug': f'category_{xml_id}'
            }
        )

        categories[xml_id] = {
            'obj': category,
            'parent_id': parent_id,
            'name': name
        }

    # Затем устанавливаем связи между категориями
    for xml_id, category_data in categories.items():
        parent_id = category_data['parent_id']
        if parent_id and parent_id in categories:
            category_data['obj'].parent = categories[parent_id]['obj']
            category_data['obj'].save()

    return categories


def parse_product_xml(categories):
    """
    Парсим файл product.xml для получения информации о товарах
    """
    url = urljoin(BASE_URL, 'product.xml')
    response = requests.get(url, auth=AUTH)
    root = ET.fromstring(response.content)

    for product_elem in root.findall('product'):
        try:
            process_product(product_elem, categories)
        except Exception as e:
            print(f"Ошибка при обработке товара: {e}")
            continue


def process_product(product_elem, categories):
    """
    Обрабатываем один товар из XML
    """
    product_id = product_elem.get('id')
    group_id = product_elem.get('groupId')
    code = product_elem.find('code').text
    name = product_elem.find('name').text
    description = product_elem.find('description').text if product_elem.find('description') is not None else ''
    price = float(product_elem.find('price').text)
    old_price = float(product_elem.find('oldprice').text) if product_elem.find('oldprice') is not None else None

    # Бренд
    brand_name = product_elem.find('brand').text if product_elem.find('brand') is not None else ''
    brand = None
    if brand_name:
        brand, _ = Brand.objects.get_or_create(
            name=brand_name,
            defaults={'slug': f'brand_{brand_name.lower().replace(" ", "_")}'}
        )

    # Основные параметры товара
    in_stock = product_elem.find('instock').text.lower() == 'true'
    quantity = int(product_elem.find('quantity').text) if product_elem.find('quantity') is not None else 0
    status = product_elem.find('status').text if product_elem.find('status') is not None else 'regular'

    # Дополнительные параметры
    material = product_elem.find('material').text if product_elem.find('material') is not None else ''
    weight = float(product_elem.find('weight').text) if product_elem.find('weight') is not None else None
    volume = float(product_elem.find('volume').text) if product_elem.find('volume') is not None else None
    barcode = product_elem.find('barcode').text if product_elem.find('barcode') is not None else ''
    is_featured = product_elem.find('featured').text.lower() == 'true' if product_elem.find(
        'featured') is not None else False
    is_bestseller = product_elem.find('bestseller').text.lower() == 'true' if product_elem.find(
        'bestseller') is not None else False
    size_type = product_elem.find('sizetype').text if product_elem.find('sizetype') is not None else ''
    composition = product_elem.find('composition').text if product_elem.find('composition') is not None else ''

    # Изображения
    small_image = product_elem.find('small_image').text if product_elem.find('small_image') is not None else ''
    big_image = product_elem.find('big_image').text if product_elem.find('big_image') is not None else ''
    super_big_image = product_elem.find('superbig_image').text if product_elem.find(
        'superbig_image') is not None else ''

    # Создаем или обновляем товар
    product, created = XMLProduct.objects.update_or_create(
        product_id=product_id,
        defaults={
            'group_id': group_id,
            'code': code,
            'name': name,
            'description': description,
            'price': price,
            'old_price': old_price,
            'brand': brand_name,
            'brand_model': brand,
            'in_stock': in_stock,
            'quantity': quantity,
            'status': status,
            'material': material,
            'weight': weight,
            'volume': volume,
            'barcode': barcode,
            'is_featured': is_featured,
            'is_bestseller': is_bestseller,
            'size_type': size_type,
            'composition': composition,
            'small_image': small_image,
            'big_image': big_image,
            'super_big_image': super_big_image,
        }
    )

    # Обрабатываем категории товара
    category_ids = [cat.get('id') for cat in product_elem.findall('category')]
    for cat_id in category_ids:
        if cat_id in categories:
            product.categories.add(categories[cat_id]['obj'])

    # Обрабатываем варианты размеров
    process_size_variants(product_elem, product)

    # Обрабатываем таблицы размеров из описания
    process_size_charts(product, description)

    # Обрабатываем дополнительные изображения
    process_attachments(product_elem, product)


def process_size_variants(product_elem, product):
    """
    Обрабатываем варианты размеров товара
    """
    for variant_elem in product_elem.findall('variant'):
        size = variant_elem.find('size').text if variant_elem.find('size') is not None else ''
        variant_price = float(variant_elem.find('price').text) if variant_elem.find(
            'price') is not None else product.price
        variant_old_price = float(variant_elem.find('oldprice').text) if variant_elem.find(
            'oldprice') is not None else product.old_price
        sku = variant_elem.find('sku').text if variant_elem.find('sku') is not None else ''
        barcode = variant_elem.find('barcode').text if variant_elem.find('barcode') is not None else ''
        quantity = int(variant_elem.find('quantity').text) if variant_elem.find('quantity') is not None else 0
        in_stock = variant_elem.find('instock').text.lower() == 'true' if variant_elem.find(
            'instock') is not None else product.in_stock

        SizeVariant.objects.update_or_create(
            product=product,
            size=size,
            defaults={
                'price': variant_price,
                'old_price': variant_old_price,
                'sku': sku,
                'barcode': barcode,
                'quantity': quantity,
                'in_stock': in_stock
            }
        )


def process_size_charts(product, description):
    """
    Извлекаем таблицы размеров из описания товара
    """
    soup = BeautifulSoup(description, 'html.parser')

    for table_div in soup.find_all('div', id='tablemer'):
        img = table_div.find('img')
        table = table_div.find('table')
        note = table_div.find('p')

        if table:
            SizeChart.objects.create(
                product=product,
                title=f"Таблица размеров для {product.name}",
                image_url=img['src'] if img else '',
                table_html=str(table),
                note=note.get_text() if note else ''
            )


def process_attachments(product_elem, product):
    """
    Обрабатываем дополнительные вложения (изображения и файлы)
    """
    attachments = []

    for attach_elem in product_elem.findall('attachment'):
        attach_type = attach_elem.get('type')
        name = attach_elem.find('name').text if attach_elem.find('name') is not None else ''

        if attach_type == 'image':
            image_url = attach_elem.find('image').text if attach_elem.find('image') is not None else ''
            attachments.append({
                'type': 'image',
                'name': name,
                'image': image_url
            })
        elif attach_type == 'file':
            file_url = attach_elem.find('file').text if attach_elem.find('file') is not None else ''
            attachments.append({
                'type': 'file',
                'name': name,
                'file': file_url
            })

    if attachments:
        product.attachments = attachments
        product.save()


def parse_stock_xml():
    """
    Парсим файл stock.xml для обновления наличия товаров
    """
    url = urljoin(BASE_URL, 'stock.xml')
    response = requests.get(url, auth=AUTH)
    root = ET.fromstring(response.content)

    for product_elem in root.findall('product'):
        product_id = product_elem.get('id')
        in_stock = product_elem.find('instock').text.lower() == 'true'
        quantity = int(product_elem.find('quantity').text) if product_elem.find('quantity') is not None else 0

        # Обновляем основной товар
        XMLProduct.objects.filter(product_id=product_id).update(
            in_stock=in_stock,
            quantity=quantity
        )

        # Обновляем варианты размеров
        for variant_elem in product_elem.findall('variant'):
            size = variant_elem.find('size').text if variant_elem.find('size') is not None else ''
            variant_in_stock = variant_elem.find('instock').text.lower() == 'true' if variant_elem.find(
                'instock') is not None else in_stock
            variant_quantity = int(variant_elem.find('quantity').text) if variant_elem.find(
                'quantity') is not None else quantity

            SizeVariant.objects.filter(
                product__product_id=product_id,
                size=size
            ).update(
                in_stock=variant_in_stock,
                quantity=variant_quantity
            )