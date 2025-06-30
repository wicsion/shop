# main/context_processors.py
from django.conf import settings

def img_src_domains(request):
    """Добавляет в контекст шаблона список разрешенных доменов для изображений"""
    return {
        'IMG_SRC_DOMAINS': settings.IMG_SRC_DOMAINS
    }