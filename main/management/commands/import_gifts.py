from django.core.management.base import BaseCommand
from  .xml_importer import GiftsXMLImporter
from django.conf import settings


class Command(BaseCommand):
    help = 'Import products from gifts.ru XML feed'

    def handle(self, *args, **options):
        importer = GiftsXMLImporter(
            login='87358_xmlexport',
            password='MGzXXSgD'
        )

        success = importer.full_import(
            site_url=settings.SITE_URL,
            ip_address=settings.SERVER_IP
        )

        if success:
            self.stdout.write(self.style.SUCCESS('Successfully imported data from gifts.ru'))
        else:
            self.stdout.write(self.style.ERROR('Failed to import data from gifts.ru'))