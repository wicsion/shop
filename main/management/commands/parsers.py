import os
from django.core.management.base import BaseCommand
from main.models import XMLProduct
from django.conf import settings


class Command(BaseCommand):
    help = 'Migrate images from URL fields to Image fields'

    def handle(self, *args, **options):
        for product in XMLProduct.objects.all():
            # Для small_image
            if product.small_image_url:
                old_path = product.small_image_url.replace(settings.MEDIA_URL, '')
                full_path = os.path.join(settings.MEDIA_ROOT, old_path)

                if os.path.exists(full_path):
                    with open(full_path, 'rb') as f:
                        product.small_image.save(os.path.basename(old_path), f, save=True)

            # Аналогично для big_image и super_big_image
            if product.big_image_url:
                old_path = product.big_image_url.replace(settings.MEDIA_URL, '')
                full_path = os.path.join(settings.MEDIA_ROOT, old_path)

                if os.path.exists(full_path):
                    with open(full_path, 'rb') as f:
                        product.big_image.save(os.path.basename(old_path), f, save=True)

            if product.super_big_image_url:
                old_path = product.super_big_image_url.replace(settings.MEDIA_URL, '')
                full_path = os.path.join(settings.MEDIA_ROOT, old_path)

                if os.path.exists(full_path):
                    with open(full_path, 'rb') as f:
                        product.super_big_image.save(os.path.basename(old_path), f, save=True)

            product.save()
            self.stdout.write(f'Processed product {product.id}')