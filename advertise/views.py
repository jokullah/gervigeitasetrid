from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.core.mail import send_mail
from django.conf import settings
from django.utils import translation  # ADD THIS IMPORT
from .forms import ProjectAdForm
from wagtail.models import Page
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import ProjectAd, ProjectPage, ProjectIndexPage

class AdvertiseView(FormView):
    template_name = "advertise/form.html"
    form_class    = ProjectAdForm
    success_url   = reverse_lazy("advertise-thanks")
    
    def form_valid(self, form):
        # CRITICAL: Don't save yet - we need to set locale first
        instance = form.save(commit=False)
        
        # Capture the current language from the request
        current_language = translation.get_language()
        instance.locale = current_language
        
        # Now save with the correct locale
        instance.save()
        
        # Debug logging
        print(f"DEBUG: Form submitted from {self.request.path}")
        print(f"DEBUG: Current language: {current_language}")
        print(f"DEBUG: Saved ProjectAd with locale: {instance.locale}")
        
        # Send notification email
        send_mail(
            subject=f"Ný verkefnaauglýsing: {instance.title}",
            message=(
                f"Fyrirtæki: {instance.company_name}\n"
                f"Tengiliður: {instance.contact_name} <{instance.contact_email}>\n"
                f"Tungumál: {instance.get_locale_display()}\n\n"  # Add locale to email
                f"Lýsing:\n{instance.description}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.PROJECT_AD_NOTIFY_TO],
        )
        
        return super().form_valid(form)

class AdvertiseThanksView(TemplateView):
    template_name = "advertise/thanks.html"
