from wagtail.models import Page, Locale
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from django.db import models
from django.shortcuts import render, redirect
from django.http import Http404
from django.urls import path
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.images.models import Image


class DepartmentIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    parent_page_types = ['home.HomePage']
    subpage_types = ['people.PeopleIndexPage']


class PeopleIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    parent_page_types = ['people.DepartmentIndexPage']
    subpage_types = ['people.PersonPage']


class PersonPage(RoutablePageMixin, Page):
    job_title = models.CharField(max_length=255, blank=True)
    email = models.EmailField()
    bio = RichTextField(blank=True)
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

    @route(r'^edit/$', name='edit')
    def edit_view(self, request):
        if not (request.user.is_authenticated and request.user.email == self.email):
            raise Http404
        
        if request.method == 'POST':
            # Update the fields for current page
            self.job_title = request.POST.get('job_title', '')
            self.bio = request.POST.get('bio', '')
            self.personal_website = request.POST.get('personal_website', '')
            
            # Handle image upload
            new_image = None
            if request.FILES.get('image'):
                # Create new image
                image_file = request.FILES['image']
                new_image = Image.objects.create(
                    title=self.title,
                    file=image_file
                )
                
                # Delete old image if it exists (will be done after updating all locales)
                old_image = self.image
                self.image = new_image
            
            # Save current page
            self.save()
            
            # Update image across all locales for this person
            if new_image:
                # Find all locale versions of this page
                if hasattr(self, 'translation_key'):
                    # Wagtail 4.1+ approach
                    locale_pages = PersonPage.objects.filter(
                        translation_key=self.translation_key
                    ).exclude(id=self.id)
                else:
                    # Fallback: find pages with same email across different locales
                    locale_pages = PersonPage.objects.filter(
                        email=self.email
                    ).exclude(id=self.id)
                
                # Update image for all locale versions
                for locale_page in locale_pages:
                    locale_page.image = new_image
                    locale_page.save()
                
                # Now delete the old image if it existed
                if old_image:
                    old_image.delete()
            
            return redirect(self.url)
        
        return render(request, 'people/person_edit.html', {'page': self})

    def get_url_parts(self, *args, **kwargs):
        url_parts = super().get_url_parts(*args, **kwargs)
        if url_parts is None:
            return None
        site_id, root_url, page_path = url_parts
        return site_id, root_url, page_path
