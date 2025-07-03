from django.core.management.base import BaseCommand
from main.models import XMLProduct
from xml.etree import ElementTree as ET
import requests
from urllib.parse import urljoin
import logging
from collections import defaultdict
from colorama import init, Fore, Back, Style

# Инициализация colorama для цветного вывода
init(autoreset=True)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import product filters from XML and apply them to products'

    def handle(self, *args, **options):
        try:
            self.stdout.write(Fore.YELLOW + "=== НАЧАЛО ИМПОРТА ФИЛЬТРОВ ===" + Style.RESET_ALL)

            # 1. Загрузка данных о фильтрах
            self.stdout.write(Fore.CYAN + "\n[1/3] Загрузка данных о фильтрах из filters.xml..." + Style.RESET_ALL)
            filters_data = self.load_filters_data()
            self.log_filters_data(filters_data)

            # 2. Загрузка данных о товарах и их фильтрах
            self.stdout.write(
                Fore.CYAN + "\n[2/3] Загрузка данных о фильтрах товаров из product.xml..." + Style.RESET_ALL)
            products_filters = self.load_products_filters()
            self.log_products_filters(products_filters)

            # 3. Применение фильтров к товарам
            self.stdout.write(Fore.CYAN + "\n[3/3] Применение фильтров к товарам..." + Style.RESET_ALL)
            self.apply_filters_to_products(filters_data, products_filters)

            self.stdout.write(Fore.GREEN + "\n=== ИМПОРТ ФИЛЬТРОВ УСПЕШНО ЗАВЕРШЕН ===" + Style.RESET_ALL)
            self.stdout.write(self.style.SUCCESS('Successfully imported and applied filters'))
        except Exception as e:
            self.stdout.write(Fore.RED + f"\nОШИБКА: {str(e)}" + Style.RESET_ALL)
            logger.error(f"Error importing filters: {str(e)}", exc_info=True)

    def log_filters_data(self, filters_data):
        """Выводит данные о фильтрах в терминал"""
        self.stdout.write(Fore.MAGENTA + f"\nЗагружено типов фильтров: {len(filters_data)}" + Style.RESET_ALL)
        for type_id, type_data in filters_data.items():
            self.stdout.write(Fore.BLUE + f"\nТип фильтра [ID: {type_id}]: " +
                              Fore.YELLOW + f"{type_data['name']}" + Style.RESET_ALL)
            self.stdout.write(f"Содержит значений: {len(type_data['filters'])}")
            for filter_id, filter_name in type_data['filters'].items():
                self.stdout.write(f"  - [ID: {filter_id}]: {filter_name}")

    def log_products_filters(self, products_filters):
        """Выводит фильтры товаров перед применением"""
        self.stdout.write(Fore.MAGENTA + f"\nНайдено товаров с фильтрами: {len(products_filters)}" + Style.RESET_ALL)
        for product_id, filters in products_filters.items():
            self.stdout.write(Fore.GREEN + f"\nТовар [ID: {product_id}]" + Style.RESET_ALL +
                              f" имеет фильтров: {len(filters)}")
            for i, f in enumerate(filters, 1):
                self.stdout.write(f"  {i}. Тип: {f.get('type_id')}, Фильтр: {f.get('filter_id')}")

    def load_filters_data(self):
        """Загружает данные о фильтрах из filters.xml"""
        filters_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/filters.xml"
        response = requests.get(filters_url)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        filters_data = defaultdict(dict)

        for filter_type in root.findall('.//filtertype'):
            type_id = filter_type.find('filtertypeid')
            type_name = filter_type.find('filtertypename')

            if type_id is not None and type_name is not None:
                type_id = type_id.text
                type_name = type_name.text
                filters_data[type_id]['name'] = type_name
                filters_data[type_id]['filters'] = {}

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
                applied_filters = []
                sizes = []

                for f in filters:
                    type_id = f.get('type_id')
                    filter_id = f.get('filter_id')

                    if type_id and filter_id and type_id in filters_data and filter_id in filters_data[type_id][
                        'filters']:
                        filter_name = filters_data[type_id]['filters'][filter_id]

                        filter_info.append({
                            'type_id': type_id,
                            'type_name': filters_data[type_id]['name'],
                            'filter_id': filter_id,
                            'filter_name': filter_name
                        })
                        applied_filters.append(f"{filters_data[type_id]['name']}: {filter_name}")

                        # Сохраняем размеры отдельно
                        if type_id == "23":  # Размеры
                            sizes.append(filter_name)

                if filter_info:
                    if not product.xml_data:
                        product.xml_data = {}

                    product.xml_data['filters'] = filter_info

                    # Обновляем поле sizes_available
                    if sizes:
                        product.sizes_available = ", ".join(sizes)
                        product.save()

                    # Вывод информации в терминал
                    self.stdout.write(Fore.GREEN + f"\nТовар [ID: {product_id}]" +
                                      Fore.YELLOW + f" {product.name}" + Style.RESET_ALL)
                    if sizes:
                        self.stdout.write(Fore.CYAN + f"Размеры: {product.sizes_available}" + Style.RESET_ALL)

            except XMLProduct.DoesNotExist:
                self.stdout.write(Fore.RED + f"\n[WARNING] Товар не найден: ID {product_id}" + Style.RESET_ALL)
            except Exception as e:
                self.stdout.write(
                    Fore.RED + f"\n[ERROR] Ошибка обработки товара {product_id}: {str(e)}" + Style.RESET_ALL)