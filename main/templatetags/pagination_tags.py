from django import template

register = template.Library()

@register.filter
def make_range(value):
    """Create a range from 1 to value"""
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return []

