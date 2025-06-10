from django import forms
from django.db import models

from wagtail.models import Page, Locale, Orderable
from wagtail.fields import RichTextField
from wagtail.search import index
from wagtail.admin.panels import MultiFieldPanel, FieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet

from modelcluster.fields import ParentalKey, ParentalManyToManyField

from base.models import TaggedItem


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        context = super().get_context(request)

        current_locale = self.locale

        blogpages = (
            BlogPage.objects.live()                    # only published
                     .filter(locale=current_locale)    # <-- locale filter
                     .order_by("-date")
        )

        context["blogpages"] = blogpages
        return context
    
    parent_page_types = ['home.HomePage']
    subpage_types = ['blog.BlogPage']


class BlogPage(Page):
    thumbnail_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)
    authors = ParentalManyToManyField('blog.Author', blank=True)

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('thumbnail_image'),
        MultiFieldPanel([
            "date",
            FieldPanel("authors", widget=forms.CheckboxSelectMultiple),
        ], heading="Blog information"),
            "intro", "body", "gallery_images",
	InlinePanel('tagged_items', label='Tags'),
        ]
    parent_page_types = ['blog.BlogIndexPage']
    subpage_types = []


class BlogPageGalleryImage(Orderable):
    page = ParentalKey(BlogPage, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = ["image", "caption"]


@register_snippet
class Author(models.Model):
    name = models.CharField(max_length=255)
    author_image = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    panels = ["name", "author_image"]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Authors'
    
