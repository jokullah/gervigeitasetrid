from django import forms
from django.db import models
from django.forms.widgets import TimeInput
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from wagtail.models import Page, Locale
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet

from modelcluster.fields import ParentalManyToManyField


class EventPage(Page):

    date = models.DateField()
    description = models.TextField()
    location = models.CharField(max_length=255)
    
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    # Fields for lectures
    host = models.CharField(max_length=255, blank=True)
    speaker = models.CharField(max_length=255, blank=True)

    event_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    ai_translated = models.BooleanField(default=False, help_text="This page was translated using AI")

    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('start_time', widget=TimeInput(format='%H:%M')),
        FieldPanel('end_time', widget=TimeInput(format='%H:%M')),
        FieldPanel('location'),
        FieldPanel('event_image'),
        FieldPanel('description'),
        FieldPanel('ai_translated'),
        MultiFieldPanel([
            FieldPanel('host'),
            FieldPanel('speaker'),
        ], heading="Lecture Fields"),
	InlinePanel('tagged_items', label='Tags'),
    ]
    parent_page_types = ['event.EventIndexPage']
    subpage_types = []


class EventIndexPage(Page):
    def get_context(self, request):
        context = super().get_context(request)

        current_locale = self.locale

        # Filter events by current language
        events = (
            EventPage.objects.live()
            .filter(locale=current_locale)
            .order_by('date')
        )

        # Pagination - 6 events per page
        page = request.GET.get('page', 1)
        paginator = Paginator(events, 6)
        try:
            events = paginator.page(page)
        except PageNotAnInteger:
            events = paginator.page(1)
        except EmptyPage:
            events = paginator.page(paginator.num_pages)

        context['events'] = events
        return context

    ai_translated = models.BooleanField(default=False, help_text="This page was translated using AI")

    content_panels = Page.content_panels + [
        FieldPanel('ai_translated'),
    ]
    
    parent_page_types = ['home.HomePage']
    subpage_types = ['event.EventPage']
