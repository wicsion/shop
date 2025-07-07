from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


class MainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'main'

    def ready(self):
        # Настройки SQLite (только для разработки)
        self._setup_sqlite()

        # Регистрация сигналов
        self._register_signals()

        logger.info(f"Приложение {self.name} инициализировано, сигналы зарегистрированы")

    def _setup_sqlite(self):
        """Настройка SQLite для улучшения производительности"""

        @receiver(connection_created)
        def setup_sqlite(sender, connection, **kwargs):
            if connection.vendor == 'sqlite':
                logger.debug("Настройка SQLite параметров...")
                cursor = connection.cursor()
                cursor.execute("PRAGMA journal_mode = WAL;")
                cursor.execute("PRAGMA cache_size = -64000;")
                cursor.execute("PRAGMA synchronous = NORMAL;")
                cursor.close()

    def _register_signals(self):
        """Явная регистрация сигналов приложения"""
        try:
            # Импортируем модуль signals для регистрации декораторов
            from . import signals  # noqa
            logger.debug("Сигналы успешно зарегистрированы")
        except ImportError as e:
            logger.error(f"Ошибка импорта сигналов: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Неожиданная ошибка при регистрации сигналов: {e}", exc_info=True)