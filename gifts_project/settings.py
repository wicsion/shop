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
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000
INSTALLED_APPS = [
    'accounts.apps.AccountsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main.apps.MainConfig',
    'designer.apps.DesignerConfig',
    'main.templatetags',
    'rest_framework',
    'django.contrib.humanize',
    'mptt',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'main.middleware.HTTP2PushMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'accounts.middleware.CartSessionMiddleware',  # Перемещено сюда
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

FIELD_ENCRYPTION_KEY = 's_I6txG2JEwhQjHHHTmYyCpu530RRUlXWt8ABfast1w='
ROOT_URLCONF = 'gifts_project.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'gifts_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'OPTIONS': {
            'timeout': 30,  # Увеличиваем таймаут
        }
    }
}

# Оптимизация для медиа-файлов
DEFAULT_FILE_STORAGE = 'gifts_projects.storage.CustomFileStorage'

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
MEDIA_ROOT = BASE_DIR / 'media'

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
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/debug.log',
            'formatter': 'verbose'
        },
        'cart_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/cart.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'cart': {
            'handlers': ['cart_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
# Настройки кеширования
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'cache'),  # Абсолютный путь
    }
}
WKHTMLTOPDF_PATH = '/usr/bin/wkhtmltopdf'
# Настройки для изображений
IMAGE_CACHE_TIMEOUT = 60 * 60 * 24 * 7  # 1 неделя

SITE_ID = 1
# Настройки компании для счетов и писем
SITE_NAME = "Мой Магазин Подарков"  # Основное название сайта
COMPANY_NAME = "ООО 'Мой Магазин Подарков'"  # Юридическое название
COMPANY_INN = "1234567890"  # ИНН компании
COMPANY_KPP = "123456789"  # КПП (если есть)
COMPANY_BANK_NAME = "ПАО 'Сбербанк'"  # Название банка
COMPANY_ACCOUNT = "40702810123456789012"  # Расчетный счет
COMPANY_COR_ACCOUNT = "30101810400000000225"  # Корр. счет
COMPANY_BANK_BIK = "044525225"  # БИК банка
try:
    from .local import *  # Для локальных переопределений
except ImportError:
    pass
