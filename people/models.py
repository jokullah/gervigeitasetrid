from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from django.db import models


class DepartmentIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    parent_page_types = ['home.HomePage']
    subpage_types = ['people.PeopleIndexPage']


class PeopleIndexPage(Page):
    intro = RichTextField(blank=True)
    textual = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    parent_page_types = ['people.DepartmentIndexPage']
    subpage_types = ['people.PersonPage']


class PersonPage(Page):
    job_title = models.CharField(max_length=255, blank=True)
    bio = RichTextField(blank=True)
    email = models.EmailField(blank=True)
    personal_website = models.URLField(blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    content_panels = Page.content_panels + [
        FieldPanel('job_title'),
        FieldPanel('bio'),
        FieldPanel('email'),
        FieldPanel('image'),
        FieldPanel('personal_website'),
    ]

    parent_page_types = ['people.PeopleIndexPage']
    subpage_types = []
