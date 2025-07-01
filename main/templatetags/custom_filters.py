from django import template

register = template.Library()

@register.filter
def resize_image(url, size='200x200'):
    return url.replace('1000x1000.jpg', f'{size}.jpg')