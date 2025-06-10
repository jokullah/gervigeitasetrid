from django import template
from base.models import Tag

register = template.Library()

@register.simple_tag
def get_all_tags():
    """Return all available tags ordered by name"""
    return Tag.objects.all().order_by('name')
