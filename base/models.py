from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.contrib.settings.models import (
    BaseGenericSetting,
    register_setting,
)
from wagtail.snippets.models import register_snippet
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
import uuid

@register_snippet
class Tag(models.Model):
    # Name field
    name = models.CharField(max_length=255, unique=True)
    
    color = models.CharField(
    max_length=7, 
    default="#3498db",
    help_text="Choose a color for this tag (hex format: #RRGGBB)"
    )
    
    panels = [
        FieldPanel("name"),
        FieldPanel("color"),
        # identifier is not included in panels since it's auto-generated
    ]
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
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
