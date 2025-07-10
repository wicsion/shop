# main/middleware.py

from urllib.parse import quote
import logging
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse

from main.models import Cart
import logging


logger = logging.getLogger(__name__)

class HTTP2PushMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith('/categories/'):  # Изменил на /categories/ для соответствия вашим URL
            # Добавляем предзагрузку для первых 8 изображений
            push_resources = []
            for product in getattr(response, 'context_data', {}).get('products', [])[:8]:
                if hasattr(product, 'main_image'):
                    img_url = reverse('main:resize_image') + f"?url={quote(product.main_image)}&width=400&height=400"
                    push_resources.append(f'<{img_url}>; rel=preload; as=image')

            if push_resources:
                response['Link'] = ', '.join(push_resources)

        return response







