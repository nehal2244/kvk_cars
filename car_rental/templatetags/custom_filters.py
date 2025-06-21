# car_rental/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def floatformat(value, decimal_places=0):
    """
    Format a float to a specific number of decimal places.
    Usage: {{ value|floatformat:2 }}
    """
    try:
        return f"{float(value):.{decimal_places}f}"
    except (ValueError, TypeError):
        return value

@register.filter
def get_item(dictionary, key):
    """
    Safely get a value from a dictionary using a key.
    Usage: {{ my_dict|get_item:"my_key" }}
    """
    return dictionary.get(key)
