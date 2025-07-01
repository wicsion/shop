import os
import re
from pathlib import Path
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.conf import settings
from main.models import XMLProduct


class Command(BaseCommand):
    help = 'Advanced image linking for products with smart matching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing image links'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed matching process'
        )
        parser.add_argument(
            '--min-id-length',
            type=int,
            default=3,
            help='Minimum product ID length to consider'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting advanced image linking..."))

        # Инициализация статистики
        stats = self.init_stats()

        # Поиск и обработка изображений
        file_groups = self.find_image_files(options, stats)

        # Привязка изображений к товарам
        self.link_images_to_products(file_groups, options, stats)

        # Вывод итогового отчета
        self.print_final_report(stats, options)

    def init_stats(self):
        """Инициализация статистики"""
        return {
            'total_files': 0,
            'products_matched': 0,
            'links_created': 0,
            'links_skipped': 0,
            'errors': 0,
            'missing_products': 0,
            'size_stats': {
                'small': {'found': 0, 'linked': 0},
                'big': {'found': 0, 'linked': 0},
                'super_big': {'found': 0, 'linked': 0},
                'other': {'found': 0, 'linked': 0}
            },
            'path_stats': defaultdict(int)
        }

    def find_image_files(self, options, stats):
        """Поиск всех изображений в медиа-директориях"""
        file_groups = defaultdict(list)
        search_paths = [
            Path(settings.MEDIA_ROOT) / 'products',
            Path(settings.MEDIA_ROOT) / 'attachments'
        ]

        for path in search_paths:
            if not path.exists():
                if options['verbose']:
                    self.stdout.write(f"Skipping non-existent path: {path}")
                continue

            for img_file in path.rglob('*.*'):
                if img_file.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.webp']:
                    continue

                product_id = self.extract_product_id(img_file.name, options['min_id_length'])
                if not product_id:
                    continue

                rel_path = str(img_file.relative_to(settings.MEDIA_ROOT))
                file_groups[product_id].append(rel_path)
                stats['total_files'] += 1
                stats['path_stats'][str(path)] += 1

                # Определяем размер изображения
                img_size = self.determine_image_size(rel_path)
                stats['size_stats'][img_size]['found'] += 1

        if options['verbose']:
            self.print_file_search_summary(stats)

        return file_groups

    def extract_product_id(self, filename, min_length=3):
        """Извлечение ID продукта из имени файла с улучшенной логикой"""
        base_name = os.path.splitext(filename)[0]

        # Основные шаблоны для извлечения ID
        patterns = [
            (r'(\d{4,})', 1),  # Последовательности из 4+ цифр
            (r'[^\d](\d{3,})[^\d]', 1),  # 3+ цифры между не-цифрами
            (r'^(\d+)[_.-]', 1),  # Цифры в начале с разделителями
            (r'[_-](\d+)[_.-]', 1),  # Цифры между разделителями
            (r'[a-z](\d{3,})', 1),  # Цифры после букв
            (r'(?:wu|ww|z)?(\d{4,})', 1),  # Префиксы wu, ww, z
            (r'product[-_]?(\d+)', 1),  # product-1234
            (r'img[-_]?(\d+)', 1),  # img-1234
            (r'^(\d+[a-z]?\d*)[_.-]', 1),  # Комбинации цифр и букв
        ]

        for pattern, group in patterns:
            if match := re.search(pattern, base_name, re.IGNORECASE):
                matched_id = match.group(group)
                if len(matched_id) >= min_length:
                    return matched_id

        return None

    def determine_image_size(self, file_path):
        """Определение размера изображения по пути"""
        file_path = file_path.lower()
        if '/small/' in file_path:
            return 'small'
        elif '/big/' in file_path:
            return 'big'
        elif '/super_big/' in file_path:
            return 'super_big'
        return 'other'

    def link_images_to_products(self, file_groups, options, stats):
        """Привязка найденных изображений к товарам"""
        for product_id, files in file_groups.items():
            try:
                xml_product = XMLProduct.objects.filter(
                    product_id=product_id,
                    was_imported=True
                ).first()

                if not xml_product:
                    stats['missing_products'] += 1
                    if options['verbose']:
                        self.stdout.write(f"Product not found: {product_id}")
                    continue

                stats['products_matched'] += 1
                self.process_product_images(xml_product, files, options, stats)

            except Exception as e:
                stats['errors'] += 1
                self.stdout.write(self.style.ERROR(
                    f"Error processing {product_id}: {str(e)}"
                ))

    def process_product_images(self, xml_product, files, options, stats):
        """Обработка изображений для конкретного товара"""
        # Группировка по размерам
        size_groups = {
            'small': [],
            'big': [],
            'super_big': [],
            'other': []
        }

        for file_path in files:
            size = self.determine_image_size(file_path)
            size_groups[size].append(file_path)

        # Привязка изображений
        for size, size_files in size_groups.items():
            if not size_files:
                continue

            best_match = self.select_best_image_match(size_files, size)
            field_name = f"{size}_image_local" if size != 'other' else 'small_image_local'

            if options['update_existing'] or not getattr(xml_product, field_name):
                setattr(xml_product, field_name, best_match)
                xml_product.save()
                stats['links_created'] += 1
                stats['size_stats'][size]['linked'] += 1

                if options['verbose']:
                    self.stdout.write(
                        f"Linked {self.style.SUCCESS(best_match)} to "
                        f"{self.style.SUCCESS(xml_product.product_id)} ({size})"
                    )
            else:
                stats['links_skipped'] += 1

    def select_best_image_match(self, file_paths, size):
        """Выбор наилучшего изображения из нескольких вариантов"""
        # Приоритет: точное соответствие размеру
        if size != 'other':
            for path in file_paths:
                if f'/{size}/' in path.lower():
                    return path

        # Приоритет: основной каталог products
        for path in file_paths:
            if '/products/' in path:
                return path

        # Возвращаем первое подходящее
        return file_paths[0]

    def print_file_search_summary(self, stats):
        """Вывод сводки по найденным файлам"""
        self.stdout.write("\n=== File Search Summary ===")
        self.stdout.write(f"Total images found: {stats['total_files']}")

        self.stdout.write("\nBy size:")
        for size, data in stats['size_stats'].items():
            self.stdout.write(f" - {size.upper()}: {data['found']} files")

        self.stdout.write("\nBy location:")
        for path, count in stats['path_stats'].items():
            self.stdout.write(f" - {path}: {count} files")

    def print_final_report(self, stats, options):
        """Итоговый отчет"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("IMAGE LINKING FINAL REPORT"))
        self.stdout.write("=" * 60)

        self.stdout.write(f"\nProducts processed: {stats['products_matched']}")
        self.stdout.write(f"Products not found: {stats['missing_products']}")
        self.stdout.write(f"Errors encountered: {stats['errors']}")

        self.stdout.write("\nFile statistics:")
        self.stdout.write(f" - Total images scanned: {stats['total_files']}")
        self.stdout.write(f" - Links created: {stats['links_created']}")
        self.stdout.write(f" - Links skipped: {stats['links_skipped']}")

        self.stdout.write("\nBy image size:")
        for size, data in stats['size_stats'].items():
            self.stdout.write(
                f" - {size.upper()}: Found {data['found']} | "
                f"Linked {data['linked']} | "
                f"Skipped {data['found'] - data['linked']}"
            )

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            "Final result: " + self.style.SUCCESS(
                f"Successfully linked {stats['links_created']} images "
                f"to {stats['products_matched']} products"
            )
        )
        self.stdout.write("=" * 60)