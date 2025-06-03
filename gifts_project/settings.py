import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _



BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-26&%&zv^7j_=s288j)0k)vf2j*kbhqv-h0ge$1=rkklhm5$g1#'


DEBUG = False

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main.apps.MainConfig',
    'accounts.apps.AccountsConfig',
    'rest_framework',
    'django.contrib.humanize',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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
        'NAME': BASE_DIR / 'db.sqlite3',
    }
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

