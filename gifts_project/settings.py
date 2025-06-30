import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _



BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-26&%&zv^7j_=s288j)0k)vf2j*kbhqv-h0ge$1=rkklhm5$g1#'


DEBUG = True
CSRF_COOKIE_SECURE = False
CSRF_USE_SESSIONS = False
SECURE_SSL_REDIRECT = False
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'accounts.apps.AccountsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main.apps.MainConfig',
    'rest_framework',
    'django.contrib.humanize',
    'django_celery_results',
    'mptt',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]
FIELD_ENCRYPTION_KEY = 's_I6txG2JEwhQjHHHTmYyCpu530RRUlXWt8ABfast1w='
ROOT_URLCONF = 'gifts_project.urls'

IMG_SRC_DOMAINS = [
    'api2.gifts.ru',
    'files.giftsoffer.ru',
    # другие домены с изображениями
]

# Обновите TEMPLATES, добавив контекстный процессор
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates',
                 BASE_DIR / 'accounts' / 'templates',
                 ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'main.context_processors.img_src_domains',  # Добавлено
            ],
        },
    },
]

WSGI_APPLICATION = 'gifts_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'railway',
        'USER': 'postgres',
        'PASSWORD': 'IbincmaWxMnrGhkUDoZQUadWzMyzcFYx',
        'HOST': 'caboose.proxy.rlwy.net',  # внешний URL (DATABASE_PUBLIC_URL)
        'PORT': '37857',
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000 -c lock_timeout=10000',
            'application_name': 'gifts_importer',
        },
        'CONN_MAX_AGE': 300,
    }
}

# Увеличиваем лимиты для bulk операций
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Настройки логирования
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.db': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]




LANGUAGE_CODE = 'ru'

LANGUAGES = [
    ('ru', _('Russian')),
    ('en', _('English')),
    ('zh-hans', _('Simplified Chinese')),
]
MODELTRANSLATION_DEFAULT_LANGUAGE = 'ru'
MODELTRANSLATION_LANGUAGES = ('ru', 'en', 'zh-hans')
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
AUTH_USER_MODEL = 'accounts.CustomUser'
TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = []
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Добавляем возможные пути
possible_paths = [
    os.path.join(BASE_DIR, 'static'),
    '/app/static',
    '/var/www/static',
]

for path in possible_paths:
    if os.path.exists(path):
        STATICFILES_DIRS.append(path)

if not STATICFILES_DIRS:
    os.makedirs(os.path.join(BASE_DIR, 'static'), exist_ok=True)
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки доступности
ACCESSIBILITY_CSS = os.path.join(STATIC_URL, 'css/accessibility.css')
ACCESSIBILITY_JS = os.path.join(STATIC_URL, 'js/accessibility.js')


# Настройки 1С интеграции
ONE_C_SYNC_URL = 'https://ваш-1с-сервер/api'
ONE_C_AUTH_TOKEN = 'ваш-токен-авторизации'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yandex.ru'  # Корректный адрес
EMAIL_PORT = 465               # Стандартный порт для SSL
EMAIL_USE_SSL = True           # Обязательно для порта 465
EMAIL_HOST_USER = 'goldinpav@yandex.ru'  # Полный email
EMAIL_HOST_PASSWORD = 'mglkpkdkfapyubfa'  # Создан в аккаунте Яндекса
DEFAULT_FROM_EMAIL = 'Уксус <goldinpav@yandex.ru>'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly'
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    ],

}

CSRF_TRUSTED_ORIGINS = [
    'https://shop-production-033f.up.railway.app/',

]

#CSRF_COOKIE_SECURE = True
#SESSION_COOKIE_SECURE = True

#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.security.csrf': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
BULK_IMPORT_SETTINGS = {
    'BATCH_SIZE': 1000,  # Размер пакета для bulk_create
    'IMAGE_PROCESSING_THREADS': 4,  # Потоки для обработки изображений
    'MAX_RETRIES': 3,  # Количество попыток при ошибках
}
IMPORT_OPTIMIZATIONS = {
    'DISABLE_AUTOCOMMIT': True,
    'SKIP_VALIDATION': True,
    'USE_FAST_UPSERT': True,
}
LOGGING['loggers']['import'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}
# Добавим в конец settings.py
SITE_URL = 'https://ваш-сайт.ru'  # Замените на реальный URL вашего сайта
SERVER_IP = 'ваш-ip'  # IP сервера, где будет работать импорт

SITE_ID = 1

# Настройки Celery
# Стало (используем публичный URL):
CELERY_BROKER_URL = 'redis://default:fnnMrTFyFWnSDJIJXSCUFIRYeelnLgOq@tramway.proxy.rlwy.net:25846/0'
CELERY_RESULT_BACKEND = 'redis://default:fnnMrTFyFWnSDJIJXSCUFIRYeelnLgOq@tramway.proxy.rlwy.net:25846/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Moscow'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 минут