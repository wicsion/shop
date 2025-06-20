from django.core.management.base import BaseCommand
from main.models import Category
import requests
from xml.etree import ElementTree as ET
from django.utils.text import slugify
from urllib.parse import urljoin
from collections import defaultdict


class Command(BaseCommand):
    help = 'Import categories from Project 111 XML feed'

    def handle(self, *args, **options):
        xml_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/treeWithoutProducts.xml"

        try:
            response = requests.get(xml_url)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            # Сначала создаем словарь всех категорий
            categories_data = {}
            parent_child_map = defaultdict(list)

            # Собираем все категории и связи родитель-потомок
            for page in root.findall('.//page'):
                page_id = page.find('page_id').text
                name = page.find('name').text
                uri = page.find('uri').text if page.find('uri') is not None else ''

                # Получаем родительскую категорию из атрибута
                parent_page_id = page.attrib.get('parent_page_id')

                categories_data[page_id] = {
                    'name': name,
                    'uri': uri,
                    'parent_page_id': parent_page_id
                }

                if parent_page_id:
                    parent_child_map[parent_page_id].append(page_id)

            # Сначала создаем все категории без родителей
            for page_id, data in categories_data.items():
                if not data['parent_page_id']:
                    self.create_category(page_id, data, None)

            # Затем создаем дочерние категории
            for parent_id in parent_child_map:
                if parent_id in categories_data:
                    parent_category = Category.objects.get(xml_id=parent_id)
                    for child_id in parent_child_map[parent_id]:
                        if child_id in categories_data:
                            self.create_category(child_id, categories_data[child_id], parent_category)

            self.stdout.write(self.style.SUCCESS('Successfully imported categories'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing categories: {str(e)}'))
            raise e

    def create_category(self, page_id, data, parent):
        name = data['name']
        uri = data['uri']

        # Формируем slug
        slug = slugify(uri) if uri else slugify(name)
        if not slug:
            slug = f'category-{page_id}'

        # Делаем slug уникальным
        original_slug = slug
        counter = 1
        while Category.objects.filter(slug=slug).exclude(xml_id=page_id).exists():
            slug = f'{original_slug}-{counter}'
            counter += 1

        category, created = Category.objects.update_or_create(
            xml_id=page_id,
            defaults={
                'name': name,
                'slug': slug,
                'parent': parent,
                'description': '',
                'is_featured': False,
                'image': '',  # В вашем XML нет информации об изображениях
                'order': 0  # Порядок можно добавить из XML если есть
            }
        )

        if created:
            self.stdout.write(f"Created category: {name} (ID: {page_id})")
        else:
            self.stdout.write(f"Updated category: {name} (ID: {page_id})")