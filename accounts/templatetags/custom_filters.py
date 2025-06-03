# accounts/templatetags/custom_filters.py
from django import template

register = template.Library()


@register.filter
def space_format(value):
    """Форматирует число с пробелами между тысячами"""
    try:
        # Пробуем преобразовать в float
        value = float(value)
    except (TypeError, ValueError):
        return value

    # Форматируем число с пробелом в качестве разделителя тысяч
    # Убираем десятичную часть если она .0
    if value.is_integer():
        return "{:,.0f}".format(value).replace(",", " ")
    return "{:,.2f}".format(value).replace(",", " ").replace(".", ",")