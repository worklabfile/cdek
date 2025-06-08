from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def subtract(value, arg):
    """Вычитает arg из value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def intcomma(value):
    """
    Converts an integer to a string containing commas every three digits.
    For example, 3000 becomes '3,000' and 45000 becomes '45,000'.
    """
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value 