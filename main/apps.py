from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.dispatch import receiver

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        # Регистрируем сигнал только после полной загрузки приложения
        @receiver(connection_created)
        def setup_sqlite(sender, connection, **kwargs):
            if connection.vendor == 'sqlite':
                cursor = connection.cursor()
                cursor.execute("PRAGMA journal_mode = WAL;")
                cursor.execute("PRAGMA cache_size = -64000;")  # Пример настройки кеша