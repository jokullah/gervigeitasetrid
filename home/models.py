from django.db import models
from django.core.paginator import Paginator
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from event.models import EventIndexPage
from django.utils.translation import gettext_lazy as _
from event.models import EventPage



class HomePage(Page):
    # add the Hero section of HomePage:
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Homepage image",
    )
    hero_text = models.CharField(
        blank=True,
        max_length=255, help_text="Write an introduction for the site"
    )
    hero_cta = models.CharField(
        blank=True,
        verbose_name="Hero CTA",
        max_length=255,
        help_text="Text to display on Call to Action",
    )
    hero_cta_link = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Hero CTA link",
        help_text="Choose a page to link to for the Call to Action",
    )

    body = RichTextField(blank=True)
    # modify your content_panels:
    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("image"),
                FieldPanel("hero_text"),
                FieldPanel("hero_cta"),
                FieldPanel("hero_cta_link"),
            ],
            heading="Hero section",
        ),
        FieldPanel('body'),
    ]


    def get_context(self, request):
        context = super().get_context(request)

        # Get all future events ordered by date
        events = EventPage.objects.live().order_by('date')
        
        # Get the page number from the query string
        page_number = request.GET.get('page', 1)
        
        # Create a paginator with 3 events per page
        paginator = Paginator(events, 3)
        events_page = paginator.get_page(page_number)
        
        context['events_page'] = events_page
        context['event_index_page'] = EventIndexPage.objects.live().first()
        
        return context

class AboutPage(Page):
    """
    A simple About Us page:
      - Page.title → the big header
      - intro_image  → a banner or portrait
      - body         → rich-text content
    """
    intro_image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("About image"),
        help_text=_("An image to introduce your organization")
    )
    body = RichTextField(
        blank=True,
        verbose_name=_("Body text"),
        help_text=_("Main content for the About Us page")
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro_image"),
        FieldPanel("body"),
    ]


