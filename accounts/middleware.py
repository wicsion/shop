# middleware.py
from django.http import HttpResponseForbidden
from .models import IPWhitelist


class IPRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_superuser:
            company = request.user.company
            allowed_ips = IPWhitelist.objects.filter(company=company).values_list('ip', flat=True)

            if allowed_ips and request.META.get('REMOTE_ADDR') not in allowed_ips:
                return HttpResponseForbidden("Доступ с этого IP запрещен")

        return self.get_response(request)