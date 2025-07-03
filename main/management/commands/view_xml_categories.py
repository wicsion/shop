from django.core.management.base import BaseCommand
import requests
from xml.etree import ElementTree as ET
from collections import defaultdict


class Command(BaseCommand):
    help = 'Вывод иерархии категорий из XML с подсчётом'

    def handle(self, *args, **options):
        xml_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/tree.xml"

        try:
            response = requests.get(xml_url)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            # Собираем все категории и связи
            categories = {}
            parent_child_map = defaultdict(list)

            for page in root.findall('.//page'):
                page_id = page.find('page_id').text if page.find('page_id') is not None else 'N/A'
                name = page.find('name').text if page.find('name') is not None else 'Без названия'
                uri = page.find('uri').text if page.find('uri') is not None else ''
                parent_id = page.attrib.get('parent_page_id', 'Корневая')

                categories[page_id] = {
                    'name': name,
                    'uri': uri,
                    'parent_id': parent_id
                }

                if parent_id:
                    parent_child_map[parent_id].append(page_id)

            # Выводим иерархию
            self.stdout.write(self.style.SUCCESS("\n=== Иерархия категорий ==="))

            def print_category(cat_id, level=0):
                cat = categories[cat_id]
                indent = "    " * level
                children_count = len(parent_child_map.get(cat_id, []))

                self.stdout.write(
                    f"{indent}├─ ID: {cat_id}, "
                    f"Название: {cat['name']}, "
                    f"URI: {cat['uri']}, "
                    f"Родитель: {cat['parent_id']}, "
                    f"Дочерних: {children_count}"
                )

                # Рекурсивно выводим дочерние категории
                for child_id in parent_child_map.get(cat_id, []):
                    print_category(child_id, level + 1)

            # Начинаем с корневых категорий (parent_id = '1' или 'Корневая')
            root_categories = [cat_id for cat_id, cat in categories.items() if cat['parent_id'] == '1']

            for root_id in root_categories:
                print_category(root_id)

            # Общая статистика
            self.stdout.write(self.style.SUCCESS("\n=== Статистика ==="))
            self.stdout.write(f"Всего категорий: {len(categories)}")
            self.stdout.write(f"Корневых категорий: {len(root_categories)}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка: {str(e)}'))