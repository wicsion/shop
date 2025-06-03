from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('accounts/', include('accounts.urls')),
]

urlpatterns += i18n_patterns(
    path('', include('main.urls')),
    # Другие URL вашего проекта
)