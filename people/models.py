from wagtail.models import Page, Locale
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel
from django.db import models
from django.shortcuts import render, redirect
from django.http import Http404
from django.urls import path
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.images.models import Image
from base.models import TaggedItem, Tag
from wagtail.search import index
from django.utils.translation import gettext_lazy as _

class PeopleIndexPage(Page):
    intro = RichTextField(blank=True)

    ai_translated = models.BooleanField(default=False, help_text="This page was translated using AI")

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('ai_translated'),
    ]

    parent_page_types = ['home.HomePage']
    subpage_types = ['people.PersonPage']

    class Meta:
        verbose_name = _("Fólksíða")
        verbose_name_plural = _("Fólksíður")


class PersonPage(RoutablePageMixin, Page):
    job_title = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=False)
    bio = RichTextField(blank=True)
    personal_website = models.URLField(blank=True)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    ai_translated = models.BooleanField(default=False, help_text="This page was translated using AI")
    
    content_panels = Page.content_panels + [
        FieldPanel('job_title'),
        FieldPanel('bio'),
        FieldPanel('email'),
        FieldPanel('image'),
        FieldPanel('personal_website'),
        FieldPanel('ai_translated'),
        InlinePanel('tagged_items', label='Tags'),
    ]

    parent_page_types = ['people.PeopleIndexPage']
    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField('bio'),
        index.SearchField('email', partial_match=True),
        index.SearchField('job_title', partial_match=True),
    ]
    
    

    @route(r'^edit/$', name='edit')
    def edit_view(self, request):
        if not (request.user.is_authenticated and request.user.email == self.email):
            raise Http404
        
        if request.method == 'POST':
            # TEXT
            self.job_title = request.POST.get('job_title', '')
            self.bio = request.POST.get('bio', '')
            self.personal_website = request.POST.get('personal_website', '')

            self.save_revision().publish()
            
            locale_pages = PersonPage.objects.filter(
                translation_key=self.translation_key
            )

            # TAGS
            selected_tag_ids = request.POST.getlist('tags')
            selected_tag_ids = [int(tag_id) for tag_id in selected_tag_ids if tag_id.isdigit()]
            selected_tags = Tag.objects.filter(id__in=selected_tag_ids)

            for locale_page in locale_pages:
                locale_page.tagged_items.all().delete()
                for tag in selected_tags:
                    locale_page.tagged_items.create(tag=tag)

            # IMAGE
            image_file = request.FILES.get('image')
            if image_file:
                new_image = Image.objects.create(
                    title=self.title, # Title of image is title of page
                    file=image_file
                )
                
                old_image = self.image
                
                # Update image for all locale versions
                for locale_page in locale_pages:
                    locale_page.image = new_image
                
                # Delete the old image if it existed
                if old_image:
                    old_image.delete()
            
            for locale_page in locale_pages:
                locale_page.save_revision().publish()

            return redirect(self.url)

        all_tags = Tag.objects.all().order_by('name_is')
        page_tag_ids = list(self.tagged_items.values_list('tag_id', flat=True))

        return render(request, 'people/person_edit.html', {
            'page': self,
            'all_tags': all_tags,
            'page_tag_ids': page_tag_ids,
        })

    class Meta:
        verbose_name = _("Starfsmannasíða")
        verbose_name_plural = _("Starfsmannasíður")
