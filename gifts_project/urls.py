from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('accounts/', include('accounts.urls')),

    # Обработка service-worker.js
    path(
        'service-worker.js',
        serve,
        {
            'document_root': settings.STATIC_ROOT,
            'path': 'js/service-worker.js'  # Путь относительно STATIC_ROOT
        },
        name='service-worker'
    ),

    path('', include('main.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path(
            'service-worker.js',
            serve,
            {
                'document_root': settings.STATICFILES_DIRS[0],
                'path': 'js/service-worker.js'
            }
        ),
    ]