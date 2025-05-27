from wagtail.models import Page
from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from django.forms.widgets import TimeInput
from taggit.models import TaggedItemBase
from modelcluster.fields import ParentalKey
from wagtail.snippets.models import register_snippet
from django.forms import CheckboxSelectMultiple
from modelcluster.fields import ParentalManyToManyField
from django import forms
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage






@register_snippet
class EventTag(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class EventPage(Page):

    date = models.DateField()
    description = models.TextField()
    location = models.CharField(max_length=255)
    
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    tags = ParentalManyToManyField("event.EventTag", blank=True)


    # Fields for public lectures
    host = models.CharField(max_length=255, blank=True)
    speaker = models.CharField(max_length=255, blank=True)

    event_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    def main_image(self):
        return self.event_image


    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('start_time', widget=TimeInput(format='%H:%M')),
        FieldPanel('end_time', widget=TimeInput(format='%H:%M')),
        FieldPanel('location'),
        FieldPanel("tags", widget=forms.CheckboxSelectMultiple),
        FieldPanel('event_image'),
        FieldPanel('description'),


        MultiFieldPanel([
            FieldPanel('host'),
            FieldPanel('speaker'),
        ], heading="Public Lecture Fields"),
    ]



class EventIndexPage(Page):
    def get_context(self, request):
        context = super().get_context(request)
        
        # Get tag from query parameter
        tag = request.GET.get('tag')
        
        # Filter events by tag if provided
        if tag:
            events = EventPage.objects.live().filter(tags__name=tag).specific()
            context['current_tag'] = tag
        else:
            events = EventPage.objects.live().order_by('date')
            
        # Sort events by date (only needed for tag filtering since we already ordered the main query)
        if tag:
            events = sorted(events, key=lambda p: p.date)
        
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


class EventTagIndexPage(Page):
    def get_context(self, request):
        # get the tag from the query string ?tag=xyz
        tag = request.GET.get('tag')

        if tag:
            events = EventPage.objects.filter(tags__name=tag).live().specific()
        else:
            events = EventPage.objects.live().specific()

        context = super().get_context(request)
        context['events'] = events
        context['current_tag'] = tag
        return context


