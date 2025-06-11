from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)
from wagtail.snippets.models import register_snippet
from django.db import models
from django.utils.translation import get_language
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
import uuid

@register_snippet
class Tag(models.Model):
    # Icelandic name (required)
    name_is = models.CharField(
        max_length=255, 
        verbose_name="Name (Icelandic)",
        help_text="Tag name in Icelandic"
    )
    
    # English name (required)
    name_en = models.CharField(
        max_length=255, 
        verbose_name="Name (English)",
        help_text="Tag name in English"
    )
    
    color = models.CharField(
        max_length=7, 
        default="#3498db",
        help_text="Choose a color for this tag (hex format: #RRGGBB)"
    )
    
    panels = [
        MultiFieldPanel([
            FieldPanel("name_is"),
            FieldPanel("name_en"),
        ], heading="Tag Names"),
        FieldPanel("color"),
    ]
    
    class Meta:
        ordering = ['name_en']
        unique_together = [('name_is', 'name_en')]
    
    def __str__(self):
        # Show both names in admin for clarity
        return f"{self.name_en} / {self.name_is}"
    
    @property
    def name(self):
        """Return the appropriate name based on current language"""
        current_language = get_language()
        if current_language and current_language.startswith('is'):
            return self.name_is
        return self.name_en
    
    def get_localized_name(self, language_code=None):
        """Get name for specific language"""
        if language_code is None:
            language_code = get_language()
        
        if language_code and language_code.startswith('is'):
            return self.name_is
        return self.name_en
    
    def get_hex_color(self):
        """Return the color as hex value"""
        return self.color
    
    def get_style_attribute(self):
        """Helper method to get inline CSS style for the tag"""
        return f"background-color: {self.color}; color: white;"

class TaggedItem(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    content_objects = ParentalKey(
        'wagtailcore.Page',
        related_name='tagged_items',
        on_delete=models.CASCADE,
    )
    
    panels = [FieldPanel('tag')]
    
    def __str__(self):
        return self.tag.name
