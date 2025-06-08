from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Вычитает arg из value."""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0 