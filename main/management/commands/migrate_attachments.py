import os
import json
from django.core.management.base import BaseCommand
from main.models import XMLProduct, ProductAttachment
from django.conf import settings
from django.core.files import File


class Command(BaseCommand):
    help = 'Migrate attachments from xml_data to ProductAttachment model'

    def handle(self, *args, **options):
        for product in XMLProduct.objects.exclude(xml_data__isnull=True):
            if 'attachments' not in product.xml_data:
                continue

            for attachment in product.xml_data['attachments']:
                if not attachment.get('image') and not attachment.get('file'):
                    continue

                file_path = attachment.get('image') or attachment.get('file')
                if not file_path:
                    continue

                # Преобразуем URL в локальный путь
                rel_path = file_path.replace(settings.MEDIA_URL, '')
                abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)

                if not os.path.exists(abs_path):
                    self.stdout.write(f"File not found: {abs_path}")
                    continue

                # Определяем тип вложения
                attachment_type = 'image' if attachment.get('image') else (
                    'document' if attachment.get('file') else 'other'
                )

                # Создаем запись в базе
                with open(abs_path, 'rb') as f:
                    pa = ProductAttachment(
                        product=product,
                        name=attachment.get('name', os.path.basename(file_path)),
                        attachment_type=attachment_type
                    )
                    pa.file.save(os.path.basename(file_path), File(f))
                    pa.save()

            self.stdout.write(f"Processed product {product.id}")