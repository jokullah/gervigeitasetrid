from wagtail.models import Page, Locale
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from django.db import models
from django.shortcuts import render, redirect
from django.http import Http404
from django.urls import path
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.images.models import Image
from base.models import Tag  # Import your Tag model
from modelcluster.fields import ParentalManyToManyField


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
    
    # Use ParentalManyToManyField instead - this is Wagtail's recommended approach
    tags = ParentalManyToManyField(
        Tag,
        blank=True,
        help_text="Select tags that apply to this person"
    )

    content_panels = Page.content_panels + [
        FieldPanel('job_title'),
        FieldPanel('bio'),
        FieldPanel('email'),
        FieldPanel('image'),
        FieldPanel('personal_website'),
        FieldPanel('tags'),  # Default Wagtail widget
    ]

    parent_page_types = ['people.PeopleIndexPage']
    subpage_types = []
    
    # Add debugging to see what's happening
    def save(self, *args, **kwargs):
        print(f"DEBUG PersonPage.save() called for {self.title}")
        print(f"DEBUG: Current tags before save: {list(self.tags.all().values_list('name', flat=True))}")
        super().save(*args, **kwargs)
        print(f"DEBUG: Current tags after save: {list(self.tags.all().values_list('name', flat=True))}")
        return self

    @route(r'^edit/$', name='edit')
    def edit_view(self, request):
        if not (request.user.is_authenticated and request.user.email == self.email):
            raise Http404
        
        if request.method == 'POST':
            # Update the fields for current page
            self.job_title = request.POST.get('job_title', '')
            self.bio = request.POST.get('bio', '')
            self.personal_website = request.POST.get('personal_website', '')
            
            # Handle tags - get the selected tag IDs and update
            selected_tag_ids = request.POST.getlist('tags')
            selected_tag_ids = [int(tag_id) for tag_id in selected_tag_ids if tag_id.isdigit()]
            print(f"DEBUG: Selected tag IDs from form: {selected_tag_ids}")
            
            locale_pages = PersonPage.objects.filter(
                translation_key=self.translation_key
            )
            
            # Update tags for all locale versions
            for locale_page in locale_pages:
                print(f"DEBUG: Setting tags for {locale_page.title}")
                locale_page.tags.set(selected_tag_ids)
                # Update other fields too for consistency
                locale_page.job_title = self.job_title
                locale_page.bio = self.bio 
                locale_page.personal_website = self.personal_website
            
            image_file = request.FILES.get('image')
            if request.FILES.get('image'):
                new_image = Image.objects.create(
                    title=self.title, # Title of image is title of page
                    file=image_file
                )
                
                old_image = self.image
                
                # Update image for all locale versions
                for locale_page in locale_pages:
                    locale_page.image = new_image
                    locale_page.save()
                
                # Delete the old image if it existed
                if old_image:
                    old_image.delete()
            else:
                # Save all locale pages if no image was uploaded
                for locale_page in locale_pages:
                    locale_page.save()
            
            return redirect(self.url)
        
        return render(request, 'people/person_edit.html', {'page': self})
