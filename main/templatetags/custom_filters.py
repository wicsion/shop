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

@register.filter
def find_variant_by_size(variants, size):
    return next((v for v in variants if v.size.upper() == size.upper()), None)

@register.filter
def split(value, arg):
    """Разделяет строку по заданному аргументу и возвращает часть после разделителя"""
    if not value or not arg:
        return value
    parts = str(value).split(arg, 1)  # Разделяем только по первому вхождению
    if len(parts) > 1:
        # Берем часть после разделителя и удаляем все HTML теги после
        result = parts[1].split('<')[0].strip()
        # Удаляем возможные точки или запятые в конце
        result = result.rstrip('.,').strip()
        return result
    return value
@register.filter
def remove_capacity(value):
    """Удаляет информацию о емкости из описания товара"""
    patterns = [
        r'<br>Емкость\s*\d+\s*мл[.,]?\s*',
        r'<br>емкость\s*\d+\s*мл[.,]?\s*',
        r'<br>Объем\s*\d+\s*мл[.,]?\s*',
        r'<br>объем\s*\d+\s*мл[.,]?\s*',
        r'Емкость\s*\d+\s*мл[.,]?\s*',
        r'емкость\s*\d+\s*мл[.,]?\s*',
        r'Объем\s*\d+\s*мл[.,]?\s*',
        r'объем\s*\d+\s*мл[.,]?\s*'
    ]
    for pattern in patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)
    return value

@register.filter
def strip(value):
    """Удаляет пробелы в начале и конце строки"""
    return value.strip() if value else value

@register.filter
def trim_spaces(value):
    """Удаляет все лишние пробелы (в начале, конце и между словами)"""
    if not value:
        return value
    return ' '.join(str(value).strip().split())

@register.filter
def get_item(form_or_dict, key):
    if hasattr(form_or_dict, 'cleaned_data'):  # Это форма Django
        return form_or_dict.cleaned_data.get(key)
    elif hasattr(form_or_dict, 'get'):  # Это словарь
        return form_or_dict.get(key)
    return None


@register.filter
def extract_capacity(value):
    """Извлекает только числовое значение и единицы измерения емкости"""
    if not value:
        return None

    # Паттерн для поиска емкости:
    # - число (может быть с пробелами, точкой или запятой как разделителями тысяч/десятичных)
    # - единицы измерения (с учетом регистра для "мАч")
    pattern = r'(\d{1,3}(?:[ \.,]?\d{3})*(?:[.,]\d+)?)\s*(мл|л|гр?|кг|см³|см3|mл|ml|g|kg|см\s*³|мАч|mAh|mA)'
    matches = re.findall(pattern, value, flags=re.IGNORECASE)

    if matches:
        # Берем первое совпадение
        number, unit = matches[0]

        # Нормализуем число:
        # - удаляем только пробелы как разделители тысяч
        # - заменяем запятую на точку для десятичных чисел
        normalized_number = number.replace(' ', '').replace(',', '.')

        # Приводим единицы измерения к стандартному виду
        unit_lower = unit.lower()
        if unit_lower in ['mah', 'мач']:
            unit = 'мАч'  # Приводим к правильному регистру
        elif unit_lower in ['ml', 'mл']:
            unit = 'мл'

        return f"{normalized_number} {unit}"

    return None
@register.filter
def ends_with(value, arg):
    """Проверяет, заканчивается ли строка на заданный аргумент"""
    if not value:
        return False
    return str(value).endswith(arg)

@register.filter
def trim(value):
    """Удаляет пробелы в начале и конце строки"""
    return value.strip() if value else value

@register.filter
def exclude_sizes(size):
    """Check if size should be excluded"""
    excluded_sizes = ['ЕДИНЫЙ РАЗМЕР', 'ONE SIZE', 'ONESIZE']
    return str(size).upper() not in excluded_sizes
