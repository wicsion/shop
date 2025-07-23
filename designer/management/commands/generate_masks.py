from django.core.management.base import BaseCommand
import os
import cv2
import numpy as np
from designer.models import CustomProductTemplate, ProductSilhouette


class Command(BaseCommand):
    help = 'Generate high-quality mask images for product templates'

    def handle(self, *args, **options):
        templates = CustomProductTemplate.objects.all()

        for template in templates:
            front_image = template.images.filter(is_front=True).first()
            if front_image and not hasattr(template, 'silhouette'):
                try:
                    input_path = front_image.image.path
                    mask_filename = f"mask_{template.id}.png"
                    output_path = os.path.join('media', 'product_silhouettes', mask_filename)
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)

                    # Чтение изображения
                    image = cv2.imread(input_path)

                    if image is None:
                        self.stdout.write(self.style.WARNING(f'Failed to read image: {input_path}'))
                        continue

                    # Альтернативный метод для сложных случаев
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                    # Размытие для уменьшения шума
                    gray = cv2.GaussianBlur(gray, (5, 5), 0)

                    # Бинаризация с высоким порогом
                    _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

                    # Находим контуры
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    # Создаем чистую маску
                    mask = np.zeros_like(gray)

                    # Заполняем контуры
                    cv2.drawContours(mask, contours, -1, (255), thickness=cv2.FILLED)

                    # Уменьшаем маску на 1 пиксель для устранения артефактов
                    mask = cv2.erode(mask, np.ones((3, 3), np.uint8), iterations=1)

                    # Инвертируем для CSS mask-image
                    mask = cv2.bitwise_not(mask)

                    # Дополнительная постобработка
                    mask = cv2.medianBlur(mask, 3)

                    # Сохраняем как PNG с максимальным качеством
                    cv2.imwrite(output_path, mask, [cv2.IMWRITE_PNG_COMPRESSION, 9])

                    ProductSilhouette.objects.create(
                        template=template,
                        mask_image=os.path.join('product_silhouettes', mask_filename)
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created high-quality mask for {template.name}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error processing {template.name}: {str(e)}'))