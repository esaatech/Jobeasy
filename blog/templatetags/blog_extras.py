from django import template
from django.utils.safestring import mark_safe

from blog.utils import normalize_blog_body

register = template.Library()


@register.filter(name="blog_body")
def blog_body_filter(value):
    return mark_safe(normalize_blog_body(value))
