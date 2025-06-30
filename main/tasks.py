import os
from io import BytesIO
import uuid
import logging
from urllib.parse import urlparse

import requests
from celery import shared_task
from django.core.files import File
from django.db.models import Q
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile

from main.models import XMLProduct

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def download_product_images(self, product_id):
    try:
        product = XMLProduct.objects.get(pk=product_id)

        def download_image(url, field):
            if not url:
                return False
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                # Генерируем уникальное имя файла
                ext = os.path.splitext(urlparse(url).path)[1] or '.jpg'
                img_name = f"{uuid.uuid4()}{ext}"

                # Сохраняем в ImageField
                img_content = BytesIO(response.content)
                field.save(img_name, File(img_content), save=False)
                return True
            except Exception as e:
                logger.error(f"Ошибка загрузки изображения {url}: {str(e)}")
                raise self.retry(exc=e, countdown=60 * self.request.retries)

        # Загружаем только если URL есть, а локальной копии нет
        if product.small_image and not product.small_image_local:
            download_image(product.small_image, product.small_image_local)
        if product.big_image and not product.big_image_local:
            download_image(product.big_image, product.big_image_local)
        if product.super_big_image and not product.super_big_image_local:
            download_image(product.super_big_image, product.super_big_image_local)

        product.save()
        return f"Images cached for product {product_id}"

    except Exception as e:
        logger.error(f"Error processing product {product_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60 * self.request.retries)


@shared_task
def cleanup_unused_images():
    """Очистка неиспользуемых изображений"""
    from django.db.models import Q
    import os
    from django.conf import settings

    # Находим все файлы изображений, на которые нет ссылок
    used_images = set()

    # Основные изображения товаров
    for product in XMLProduct.objects.exclude(Q(small_image_local='') | Q(small_image_local__isnull=True)):
        used_images.add(product.small_image_local.path)
    for product in XMLProduct.objects.exclude(Q(big_image_local='') | Q(big_image_local__isnull=True)):
        used_images.add(product.big_image_local.path)
    for product in XMLProduct.objects.exclude(Q(super_big_image_local='') | Q(super_big_image_local__isnull=True)):
        used_images.add(product.super_big_image_local.path)

    # Дополнительные изображения
    for product in XMLProduct.objects.exclude(attachments_local__isnull=True):
        for attachment in product.attachments_local:
            if attachment['type'] == 'image':
                used_images.add(os.path.join(settings.MEDIA_ROOT, attachment['file']))

    # Удаляем неиспользуемые файлы
    for root, dirs, files in os.walk(os.path.join(settings.MEDIA_ROOT, 'products')):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path not in used_images:
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    return "Unused images cleanup completed"