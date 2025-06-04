from django import template

register = template.Library()

@register.filter
def floatformat(value, decimal_places=0):
    try:
        return f"{float(value):.{decimal_places}f}"
    except (ValueError, TypeError):
        return value


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# car_rental/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
