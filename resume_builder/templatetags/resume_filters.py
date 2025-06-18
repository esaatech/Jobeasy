from django import template

register = template.Library()

@register.filter(name='trim')
def trim(value):
    """Removes leading and trailing whitespace."""
    return value.strip() if value else value