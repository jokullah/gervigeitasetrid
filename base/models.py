from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)

from wagtail.snippets.models import register_snippet
from django.db import models

@register_setting
class FooterText(BaseGenericSetting):
    body = RichTextField()

    panels = [
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "Footer text"
        verbose_name_plural = "Footer text"

@register_snippet
class Tag(models.Model):
	name = models.CharField(max_length=255, unique=True)

	panels = [FieldPanel("name")]

	def __str__(self):
		return self.name
