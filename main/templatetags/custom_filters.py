from django import template
import re
register = template.Library()

@register.filter
def resize_image(url, size='200x200'):
    return url.replace('1000x1000.jpg', f'{size}.jpg')

@register.filter
def is_list(value):
    return isinstance(value, list)

@register.filter
def get_variant_quantity(product, size):
    return product.get_variant_quantity(size)


# Добавляем новый фильтр
@register.filter
def get_variant_by_size(variants, size):
    return variants.filter(size=size).first()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_variant_quantity(product, size):
    """Возвращает количество для варианта с указанным размером"""
    if product.variants.exists():
        variant = product.variants.filter(size=size).first()
        return variant.quantity if variant else 0
    elif product.xml_data and 'attributes' in product.xml_data and 'size_options' in product.xml_data['attributes']:
        return product.xml_data['attributes']['size_options'].get(size, {}).get('quantity', product.quantity)
    return product.quantity

@register.filter
def cut(value, arg):
    """Удаляет все вхождения arg из строки value"""
    return value.replace(arg, '')

@register.filter
def remove_tablemer(value):
    """Удаляет только таблицу, но сохраняет остальной текст в div#tablemer"""
    # Удаляем таблицу и изображение, но сохраняем текст перед/после
    value = re.sub(r'<img[^>]*>', '', value)  # Удаляем изображение
    value = re.sub(r'<table[^>]*>.*?</table>', '', value, flags=re.DOTALL)  # Удаляем таблицу
    return value