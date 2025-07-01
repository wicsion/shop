from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
import os
from main.models import XMLProduct


class Command(BaseCommand):
    help = 'Rename product images to consistent format'

    def handle(self, *args, **options):
        total_products = XMLProduct.objects.count()

        if total_products == 0:
            self.stdout.write(self.style.ERROR("В базе нет товаров!"))
            return

        self.stdout.write(f"Всего товаров в базе: {total_products}")

        products_with_images = XMLProduct.objects.filter(small_image_local__isnull=False)
        self.stdout.write(f"Товаров с small_image_local: {products_with_images.count()}")

        processed = 0
        renamed = 0
        skipped_missing = 0
        errors = 0

        for product in products_with_images:
            try:
                processed += 1
                old_path = product.small_image_local.path

                if not os.path.exists(old_path):
                    skipped_missing += 1
                    self.stdout.write(self.style.WARNING(
                        f"[{processed}/{total_products}] Файл отсутствует: {old_path}"
                    ))
                    continue

                new_name = f"product_{product.product_id}_small.jpg"
                new_dir = os.path.join("media", "products", "small")
                os.makedirs(new_dir, exist_ok=True)  # Создаём папку если её нет
                new_path = os.path.join(new_dir, new_name)

                os.rename(old_path, new_path)
                with open(new_path, 'rb') as f:
                    product.small_image_local.save(new_name, ContentFile(f.read()), save=True)

                renamed += 1
                self.stdout.write(self.style.SUCCESS(
                    f"[{processed}/{total_products}] Переименовано: {os.path.basename(old_path)} -> {new_name}"
                ))

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(
                    f"Ошибка с товаром ID {product.id}: {str(e)}"
                ))

        # Итоговая статистика
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("РЕЗУЛЬТАТ"))
        self.stdout.write("=" * 50)
        self.stdout.write(f"Всего товаров: {total_products}")
        self.stdout.write(f"Обработано: {processed}")
        self.stdout.write(f"Успешно переименовано: {renamed}")
        self.stdout.write(f"Пропущено (нет файла): {skipped_missing}")
        self.stdout.write(f"Ошибок: {errors}")
        self.stdout.write("=" * 50)