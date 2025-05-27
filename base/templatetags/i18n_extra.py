from django import template
from wagtail.models import Locale          # ← NEW import

register = template.Library()


@register.filter
def translate_page(page, lang_code):
    """
    Return ``page`` translated into `lang_code`
    (eg. "en", "is").  If that translation doesn't exist,
    fall back to the original ``page``.
    """
    if not page:                     # already None / ""
        return page

    try:
        locale = Locale.objects.get(language_code=lang_code[:2])
        return page.get_translation(locale)
    except (Locale.DoesNotExist, page.__class__.DoesNotExist, AttributeError):
        return page                  # graceful fallback
