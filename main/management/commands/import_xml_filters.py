from django.core.management.base import BaseCommand
from main.models import XMLProduct
from xml.etree import ElementTree as ET
import requests
from urllib.parse import urljoin
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import product filters from XML and apply them to products'

    def handle(self, *args, **options):
        try:
            # 1. Загрузка данных о фильтрах
            filters_data = self.load_filters_data()

            # 2. Загрузка данных о товарах и их фильтрах
            products_filters = self.load_products_filters()

            # 3. Применение фильтров к товарам
            self.apply_filters_to_products(filters_data, products_filters)

            self.stdout.write(self.style.SUCCESS('Successfully imported and applied filters'))
        except Exception as e:
            logger.error(f"Error importing filters: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'Error importing filters: {str(e)}'))

    def load_filters_data(self):
        """Загружает данные о фильтрах из filters.xml"""
        filters_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/filters.xml"
        response = requests.get(filters_url)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        filters_data = defaultdict(dict)

        # Парсим типы фильтров
        for filter_type in root.findall('.//filtertype'):
            type_id = filter_type.find('filtertypeid')
            type_name = filter_type.find('filtertypename')

            if type_id is not None and type_name is not None:
                type_id = type_id.text
                type_name = type_name.text
                filters_data[type_id]['name'] = type_name
                filters_data[type_id]['filters'] = {}

                # Парсим значения фильтров для каждого типа
                for filter_item in filter_type.findall('.//filter'):
                    filter_id = filter_item.find('filterid')
                    filter_name = filter_item.find('filtername')

                    if filter_id is not None and filter_name is not None:
                        filter_id = filter_id.text
                        filter_name = filter_name.text
                        filters_data[type_id]['filters'][filter_id] = filter_name

        return filters_data

    def load_products_filters(self):
        """Загружает данные о фильтрах товаров из product.xml"""
        products_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/product.xml"
        response = requests.get(products_url)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        products_filters = {}

        for product in root.findall('.//product'):
            product_id_element = product.find('product_id')
            if product_id_element is None:
                continue

            product_id = product_id_element.text
            if not product_id:
                continue

            filters = []

            # Получаем фильтры товара
            for filter_element in product.findall('.//filters/filter'):
                filter_type = filter_element.find('filtertypeid')
                filter_id = filter_element.find('filterid')

                if filter_type is not None and filter_id is not None:
                    filter_type = filter_type.text
                    filter_id = filter_id.text
                    filters.append({
                        'type_id': filter_type,
                        'filter_id': filter_id
                    })

            if filters:
                products_filters[product_id] = filters

        return products_filters

    def apply_filters_to_products(self, filters_data, products_filters):
        """Применяет фильтры к товарам и сохраняет в базу"""
        for product_id, filters in products_filters.items():
            try:
                product = XMLProduct.objects.get(product_id=product_id)
                filter_info = []

                # Формируем информацию о фильтрах
                for f in filters:
                    type_id = f.get('type_id')
                    filter_id = f.get('filter_id')

                    if type_id and filter_id and type_id in filters_data and filter_id in filters_data[type_id][
                        'filters']:
                        filter_info.append({
                            'type_id': type_id,
                            'type_name': filters_data[type_id]['name'],
                            'filter_id': filter_id,
                            'filter_name': filters_data[type_id]['filters'][filter_id]
                        })

                # Обновляем данные товара
                if filter_info:
                    if not product.xml_data:
                        product.xml_data = {}

                    product.xml_data['filters'] = filter_info
                    product.save()

                    self.stdout.write(f"Applied filters to product {product_id}")

            except XMLProduct.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Product {product_id} not found in database"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing product {product_id}: {str(e)}"))