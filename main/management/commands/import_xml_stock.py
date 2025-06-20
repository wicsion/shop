from django.core.management.base import BaseCommand
from main.models import XMLProduct
import requests
from xml.etree import ElementTree as ET


class Command(BaseCommand):
    help = 'Update product stock from Project 111 XML feed'

    def handle(self, *args, **options):
        xml_url = "https://87358_xmlexport:MGzXXSgD@api2.gifts.ru/export/v2/catalogue/stock.xml"

        try:
            response = requests.get(xml_url)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            self.update_stock(root)

            self.stdout.write(self.style.SUCCESS('Successfully updated stock information'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error updating stock: {str(e)}'))

    def update_stock(self, root):
        for stock in root.findall('stock'):
            product_id = stock.find('product_id').text
            free = int(stock.find('free').text) if stock.find('free') is not None else 0

            try:
                product = XMLProduct.objects.get(product_id=product_id)
                product.quantity = free
                product.in_stock = free > 0
                product.save()
            except XMLProduct.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Товар {product_id} не найден. Пропускаем...'))