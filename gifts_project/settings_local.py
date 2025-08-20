import os
from .settings import *


DEBUG = False
SECRET_KEY = '_=2vux#q(*dx9t4ot-o_k3*uy8!)msoh32n3c@d0q3c$8dsd+@'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = False  # True после настройки SSL
ALLOWED_HOSTS = ['51.250.70.194', 'winwindeal.ru', 'www.winwindeal.ru']

# База данных (PostgreSQL вместо SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gifts_db',
        'USER': 'gifts_user',
        'PASSWORD': 'vladnext232',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Email (для продакшена)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'goldinpav@yandex.ru'
EMAIL_HOST_PASSWORD = 'mglkpkdkfapyubfa'  # Пароль приложения
DEFAULT_FROM_EMAIL = 'Уксус <goldinpav@yandex.ru>'

# Логирование (для продакшена)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/error.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}