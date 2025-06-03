from wagtail.models import Page
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
            # Update the fields
            self.job_title = request.POST.get('job_title', '')
            self.bio = request.POST.get('bio', '')
            self.personal_website = request.POST.get('personal_website', '')
            
            # Handle image upload
            if request.FILES.get('image'):
                # Delete old image if it exists
                if self.image:
                    old_image = self.image
                    self.image = None
                    old_image.delete()
                
                # Create new image
                image_file = request.FILES['image']
                image = Image.objects.create(
                    title=self.title,
                    file=image_file
                )
                self.image = image
            
            self.save()
            return redirect(self.url)
        return render(request, 'people/person_edit.html', {'page': self})

    def get_url_parts(self, *args, **kwargs):
        url_parts = super().get_url_parts(*args, **kwargs)
        if url_parts is None:
            return None
        site_id, root_url, page_path = url_parts
        return site_id, root_url, page_path
