# Create this file: search/templatetags/search_extras.py
# (create the templatetags directory and __init__.py file if they don't exist)

from django import template
from django.utils.translation import gettext as _

register = template.Library()

@register.filter
def verbose_name(obj):
    """
    Returns the verbose name of a model instance
    """
    try:
        # Get the verbose name from the model's meta
        verbose_name = str(obj._meta.verbose_name)
        
        # Debug: if it's showing "síða", something is wrong
        if verbose_name.lower() == 'síða':
            # Try to get the actual model class and its verbose name
            model_class = obj.__class__
            if hasattr(model_class._meta, 'verbose_name'):
                return str(model_class._meta.verbose_name)
        
        return verbose_name
    except (AttributeError, Exception) as e:
        # Fallback: return the class name cleaned up
        class_name = obj.__class__.__name__
        if class_name.lower().endswith('page'):
            return class_name[:-4].title()
        return class_name

@register.filter  
def verbose_name_plural(obj):
    """
    Returns the verbose name plural of a model instance
    """
    try:
        return str(obj._meta.verbose_name_plural)
    except AttributeError:
        return obj.__class__.__name__

@register.filter
def debug_model_info(obj):
    """
    Debug filter to see what's happening with the model
    """
    try:
        return f"Model: {obj.__class__.__name__}, Verbose: {obj._meta.verbose_name}, App: {obj._meta.app_label}"
    except:
        return f"Error getting model info for {obj}"
