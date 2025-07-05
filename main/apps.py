from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.dispatch import receiver

class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        # Регистрируем сигналы SQLite
        @receiver(connection_created)
        def setup_sqlite(sender, connection, **kwargs):
            if connection.vendor == 'sqlite':
                cursor = connection.cursor()
                cursor.execute("PRAGMA journal_mode = WAL;")
                cursor.execute("PRAGMA cache_size = -64000;")

        # Импортируем сигналы после полной загрузки приложения
        try:
            import main.signals
        except ImportError as e:
            print(f"Error importing signals: {e}")  # Для отладки