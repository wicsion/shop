from django.core.management.base import BaseCommand
from main.models import XMLProduct
import requests
from xml.etree import ElementTree as ET
import json


class Command(BaseCommand):
    help = 'Import product filters from XML feed'

    def handle(self, *args, **options):
        filters_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/filters.xml"

        try:
            # Сначала загружаем справочник фильтров
            response = requests.get(filters_url)
            response.raise_for_status()
            filters_root = ET.fromstring(response.content)

            # Создаем словарь фильтров {id: name}
            filters_dict = {}
            for filter_type in filters_root.findall('filtertype'):
                filter_type_id = filter_type.find('filtertypeid').text
                filter_type_name = filter_type.find('name').text
                filters_dict[filter_type_id] = filter_type_name

            # Обновляем фильтры для каждого товара
            updated_count = 0

            # Берем товары пачками по 100 для оптимизации
            for product in XMLProduct.objects.all().iterator(chunk_size=100):
                if not product.xml_data:
                    continue

                if 'filters' in product.xml_data:
                    # Обновляем имена фильтров
                    for f in product.xml_data['filters']:
                        if f['type'] in filters_dict:
                            f['type_name'] = filters_dict[f['type']]

                    product.xml_data['filters'] = product.xml_data['filters']
                    product.save()
                    updated_count += 1

            self.stdout.write(self.style.SUCCESS(
                f'Filters updated for {updated_count} products'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing filters: {str(e)}'))