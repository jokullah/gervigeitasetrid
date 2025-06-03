from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.core.mail import send_mail
from django.conf import settings
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
        instance = form.save()               # write to DB
        # notify admin
        send_mail(
            subject=f"Ný verkefnaauglýsing: {instance.title}",
            message=(
                f"Fyrirtæki: {instance.company_name}\n"
                f"Tengiliður: {instance.contact_name} <{instance.contact_email}>\n\n"
                f"Lýsing:\n{instance.description}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.PROJECT_AD_NOTIFY_TO],
        )
        return super().form_valid(form)


class AdvertiseThanksView(TemplateView):
    template_name = "advertise/thanks.html"
