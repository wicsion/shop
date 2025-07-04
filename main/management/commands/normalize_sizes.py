from django.core.management.base import BaseCommand
from main.models import XMLProduct


class Command(BaseCommand):
    help = 'Normalize product sizes'

    def handle(self, *args, **options):
        for product in XMLProduct.objects.all():
            product.save()  # Это вызовет clean_sizes() и нормализацию
            self.stdout.write(f"Processed: {product.name}")