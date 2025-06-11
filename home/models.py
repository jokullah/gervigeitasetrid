from django.db import models
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy

from wagtail.models import Page, Locale
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

from event.models import EventPage, EventIndexPage
from blog.models import BlogPage


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

    ai_translated = models.BooleanField(default=False, help_text="This page was translated using AI")

    body = RichTextField(blank=True)
    # modify your content_panels:
    content_panels = Page.content_panels + [
        FieldPanel('ai_translated'),
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

        current_locale = Locale.objects.get(language_code=request.LANGUAGE_CODE)

        # Get all future events ordered by date
        events = EventPage.objects.live().filter(locale=current_locale).order_by('date')
        
        # Get the page number from the query string
        page_number = request.GET.get('page', 1)
        
        # Create a paginator with 3 events per page
        paginator = Paginator(events, 3)
        events_page = paginator.get_page(page_number)
        
        context['events_page'] = events_page
        context['event_index_page'] = EventIndexPage.objects.live().first()

        # Get the current locale
        current_locale = getattr(request, "locale", None)
        if current_locale is None:
            current_locale = Locale.objects.get(language_code=request.LANGUAGE_CODE[:2])

        # Get latest 6 blog posts
        latest_posts = (
            BlogPage.objects.live()
            .filter(locale=current_locale)
            .order_by('-date', '-first_published_at')[:6]
        )
        context['latest_posts'] = latest_posts
        
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
        verbose_name=gettext_lazy("About image"),
        help_text=gettext_lazy("An image to introduce your organization")
    )
    body = RichTextField(
        blank=True,
        verbose_name=gettext_lazy("Body text"),
        help_text=gettext_lazy("Main content for the About Us page")
    )

    ai_translated = models.BooleanField(default=False, help_text="This page was translated using AI")

    content_panels = Page.content_panels + [
        FieldPanel("intro_image"),
        FieldPanel("body"),
        FieldPanel('ai_translated'),
    ]

    parent_page_types = ['home.HomePage']
    subpage_types = []

class SupporterBlock(blocks.StructBlock):
    name = blocks.CharBlock(required=True)
    logo = ImageChooserBlock(required=False)
    website = blocks.URLBlock(required=False)

    class Meta:
        icon = "user"
        label = "Supporter"

class SupportersPage(Page):
    intro = RichTextField(blank=True)
    supporters = StreamField([
        ('supporter', SupporterBlock())
    ], blank=True)

    ai_translated = models.BooleanField(default=False, help_text="This page was translated using AI")

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('supporters'),
        FieldPanel('ai_translated'),
    ]

    parent_page_types = ['home.HomePage']
    subpage_types = []

