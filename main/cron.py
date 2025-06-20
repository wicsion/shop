from django_cron import CronJobBase, Schedule
from django.core.management import call_command


class ImportProductsJob(CronJobBase):
    RUN_EVERY_MINS = 1440  # Every 24 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'main.import_products_job'

    def do(self):
        call_command('import_xml_products')


class ImportStockJob(CronJobBase):
    RUN_EVERY_MINS = 60  # Every hour

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'main.import_stock_job'

    def do(self):
        call_command('import_xml_stock')


class ImportCategoriesJob(CronJobBase):
    RUN_EVERY_MINS = 1440  # Every 24 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'main.import_categories_job'

    def do(self):
        call_command('import_xml_categories')