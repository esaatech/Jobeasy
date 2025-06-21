from django import template
import json
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter(name='safe_json')
def safe_json(obj):
    if obj is None:
        return mark_safe('null')
    
    # Convert Django models to dictionaries
    if hasattr(obj, '__dict__'):
        # A simple way to serialize model data, excluding internal fields
        data = {key: value for key, value in obj.__dict__.items() if not key.startswith('_')}
        return mark_safe(json.dumps(data, cls=DjangoJSONEncoder))

    return mark_safe(json.dumps(obj, cls=DjangoJSONEncoder))
