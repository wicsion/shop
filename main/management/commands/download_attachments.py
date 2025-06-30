import os
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from django.conf import settings
from main.models import XMLProduct
from pathlib import Path
from urllib.parse import urlparse


class Command(BaseCommand):
    help = 'Докачка отсутствующих изображений (оптимизированная версия)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--threads',
            type=int,
            default=5,  # Уменьшено по умолчанию
            help='Количество потоков (по умолчанию: 5)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=2000,  # Уменьшено по умолчанию
            help='Лимит загрузки (по умолчанию: 2000)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.5,
            help='Задержка между запросами (по умолчанию: 0.5 сек)'
        )

    def handle(self, *args, **options):
        self.stdout.write("Начинаем процесс докачки изображений...")
        self.download_remaining(
            max_workers=options['threads'],
            limit=options['limit'],
            delay=options['delay']
        )

    def generate_filename(self, product_id, file_url):
        """Генерация имени файла в формате ID_НАЗВАНИЕ"""
        filename = file_url.split('/')[-1]
        return f"{product_id}_{filename}"

    def download_file(self, args):
        """Загрузка одного файла с обработкой ошибок"""
        product_id, file_url, attachments_dir, delay = args
        try:
            filename = self.generate_filename(product_id, file_url)
            filepath = Path(attachments_dir) / filename

            if filepath.exists():
                return (filename, "exists")

            # Добавляем случайную задержку
            time.sleep(delay * random.uniform(0.5, 1.5))

            clean_url = file_url.replace('87358_xmlexport:MGzXXSgD@', '')

            response = requests.get(
                clean_url,
                auth=('87358_xmlexport', 'MGzXXSgD'),
                timeout=30,
                stream=True
            )
            response.raise_for_status()

            temp_path = filepath.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            temp_path.rename(filepath)
            return (filename, "downloaded")

        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 429:
                # Возвращаем URL для повторной попытки
                return (filename, "retry")
            return (filename, f"error: {str(e)}")
        except Exception as e:
            return (filename, f"error: {str(e)}")

    def download_remaining(self, max_workers=5, limit=2000, delay=0.5):
        attachments_dir = Path(settings.MEDIA_ROOT) / 'attachments'
        attachments_dir.mkdir(exist_ok=True, parents=True)

        # Собираем отсутствующие файлы
        missing_files = []
        for product in XMLProduct.objects.iterator():
            attachments = product.xml_data.get('attributes', {}).get('attachments', [])
            for att in attachments:
                if att.get('type') == 'image':
                    file_url = att.get('image') or att.get('file')
                    if file_url:
                        filename = self.generate_filename(product.product_id, file_url)
                        if not (attachments_dir / filename).exists():
                            missing_files.append((product.product_id, file_url, str(attachments_dir), delay))

        total_missing = len(missing_files)
        self.stdout.write(f"Всего файлов для загрузки: {total_missing}")
        self.stdout.write(f"Будет загружено: {min(limit, total_missing)}")
        self.stdout.write(f"Используем {max_workers} потоков с задержкой {delay} сек...\n")

        results = {'exists': 0, 'downloaded': 0, 'errors': 0, 'retries': []}
        processed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.download_file, task): task
                for task in missing_files[:limit]
            }

            for future in as_completed(futures):
                filename, status = future.result()
                processed += 1

                if status == "exists":
                    results['exists'] += 1
                elif status == "downloaded":
                    results['downloaded'] += 1
                    if results['downloaded'] % 100 == 0:
                        self.stdout.write(f"Загружено: {results['downloaded']}/{min(limit, total_missing)}")
                elif status == "retry":
                    results['retries'].append(futures[future])
                else:
                    results['errors'] += 1
                    self.stdout.write(f"Ошибка: {filename} - {status}")

                if processed % 100 == 0:
                    self.stdout.write(f"Обработано: {processed}/{min(limit, total_missing)}")

        # Повторная попытка для ошибок 429
        if results['retries']:
            self.stdout.write(f"\nПовторная попытка для {len(results['retries'])} файлов...")
            with ThreadPoolExecutor(max_workers=2) as executor:  # Еще меньше потоков для повторных попыток
                retry_futures = {
                    executor.submit(self.download_file, task): task
                    for task in results['retries']
                }

                for future in as_completed(retry_futures):
                    filename, status = future.result()
                    if status == "downloaded":
                        results['downloaded'] += 1
                        results['retries'].remove(retry_futures[future])
                    else:
                        results['errors'] += 1

        # Итоговый отчет
        self.stdout.write("\nРезультаты:")
        self.stdout.write(f"• Уже существовало: {results['exists']}")
        self.stdout.write(f"• Успешно загружено: {results['downloaded']}")
        self.stdout.write(f"• Ошибок: {results['errors']}")
        self.stdout.write(f"• Осталось докачать: {total_missing - results['downloaded']}")