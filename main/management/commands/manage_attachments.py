import os
import re
import csv
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from main.models import XMLProduct, ProductAttachment
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Link downloaded images to products with detailed report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report',
            type=str,
            default='image_link_report.csv',
            help='Output CSV report filename'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for processing'
        )

    def handle(self, *args, **options):
        report_file = options['report']
        batch_size = options['batch_size']

        base_dirs = {
            'small': os.path.join(settings.MEDIA_ROOT, 'products', 'small'),
            'big': os.path.join(settings.MEDIA_ROOT, 'products', 'big'),
            'super_big': os.path.join(settings.MEDIA_ROOT, 'products', 'super_big'),
            'attachments': os.path.join(settings.MEDIA_ROOT, 'attachments')
        }

        # Улучшенное регулярное выражение
        pattern = re.compile(
            r'^(?:(?P<product_id>\d+)_)?'  # ID товара (опционально)
            r'(?:(?P<price>[\d\.]+)_)?'  # Цена (опционально)
            r'(?P<article>[a-zA-Z0-9]+)?'  # Артикул
            r'(?:_(?P<variant>\d+))?'  # Номер варианта
            r'(?:\.(?P<ext>tif|jpg|png))?'  # Расширение
            r'(?:_(?P<res>\d+x\d+))?'  # Разрешение
            r'\.(?:jpg|png)$'  # Конечное расширение
        )

        # Подготовка отчёта
        with open(report_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'filename',
                'product_id',
                'article',
                'found_product_id',
                'status',
                'image_type',
                'error_message'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for img_type, dir_path in base_dirs.items():
                if not os.path.exists(dir_path):
                    logger.warning(f"Directory not found: {dir_path}")
                    continue

                logger.info(f"\nProcessing {img_type} images in {dir_path}...")
                processed_files = 0

                for filename in os.listdir(dir_path):
                    row = {
                        'filename': filename,
                        'product_id': '',
                        'article': '',
                        'found_product_id': '',
                        'status': 'SKIPPED',
                        'image_type': img_type,
                        'error_message': ''
                    }

                    try:
                        match = pattern.match(filename)
                        if not match:
                            row['error_message'] = 'Filename pattern mismatch'
                            writer.writerow(row)
                            continue

                        data = match.groupdict()
                        product = None
                        search_method = ''

                        # Поиск по product_id (если есть)
                        if data.get('product_id'):
                            product = XMLProduct.objects.filter(
                                product_id=data['product_id']
                            ).first()
                            if product:
                                search_method = 'by product_id'
                                row['product_id'] = data['product_id']
                                row['found_product_id'] = product.product_id

                        # Поиск по article (с обработкой для SQLite)
                        if not product and data.get('article'):
                            # Сначала точное совпадение по коду
                            product = XMLProduct.objects.filter(
                                code=data['article']
                            ).first()
                            if product:
                                search_method = 'by exact article match'
                            else:
                                # Поиск в alt_ids (для SQLite)
                                products = XMLProduct.objects.all()
                                for p in products:
                                    if data['article'] in p.alt_ids:
                                        product = p
                                        search_method = 'by alt_id'
                                        break

                            if product:
                                row['article'] = data['article']
                                row['found_product_id'] = product.product_id

                        if not product:
                            row['status'] = 'FAILED'
                            row['error_message'] = 'Product not found'
                            writer.writerow(row)
                            continue

                        # Обработка файла
                        file_path = os.path.join(dir_path, filename)
                        rel_path = os.path.relpath(file_path, settings.MEDIA_ROOT)

                        if img_type == 'small':
                            product.small_image = rel_path
                        elif img_type == 'big':
                            product.big_image = rel_path
                        elif img_type == 'super_big':
                            product.super_big_image = rel_path
                        else:  # attachments
                            ProductAttachment.objects.create(
                                product=product,
                                file=rel_path,
                                name=filename,
                                attachment_type='image'
                            )

                        product.save()
                        row['status'] = f'LINKED ({search_method})'
                        processed_files += 1

                        if processed_files % batch_size == 0:
                            logger.info(f"Processed {processed_files} files...")

                    except Exception as e:
                        row['status'] = 'ERROR'
                        row['error_message'] = str(e)
                        logger.error(f"Error processing {filename}: {str(e)}")

                    writer.writerow(row)

        # Вывод итогов
        logger.info("\n" + "=" * 50)
        logger.info(f"Report generated: {os.path.abspath(report_file)}")
        self.print_summary(report_file)

    def print_summary(self, report_file):
        """Выводит статистику по результатам"""
        with open(report_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        total = len(rows)
        linked = sum(1 for row in rows if row['status'].startswith('LINKED'))
        failed = sum(1 for row in rows if row['status'] == 'FAILED')
        errors = sum(1 for row in rows if row['status'] == 'ERROR')
        skipped = sum(1 for row in rows if row['status'] == 'SKIPPED')

        self.stdout.write("\nSummary:")
        self.stdout.write(f"Total files processed: {total}")
        self.stdout.write(self.style.SUCCESS(f"Successfully linked: {linked}"))
        self.stdout.write(self.style.WARNING(f"Products not found: {failed}"))
        self.stdout.write(self.style.ERROR(f"Errors occurred: {errors}"))
        self.stdout.write(f"Skipped files: {skipped}")