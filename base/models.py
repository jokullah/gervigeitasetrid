from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)

@register_setting
class FooterText(BaseGenericSetting):
    body = RichTextField()

    panels = [
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "Footer text"
        verbose_name_plural = "Footer text"
