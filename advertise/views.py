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
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

class AdvertiseView(FormView):
    template_name = "advertise/form.html"
    form_class    = ProjectAdForm
    success_url   = reverse_lazy("advertise:advertise-thanks")  # Fixed: Added namespace

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


@login_required
@require_POST
@csrf_protect
def assign_to_project(request, page_id):
    """
    Assign the current user (must be in Starfsmenn group) to a project as leidbeinandi
    """
    # Check if user is in Starfsmenn group
    if not request.user.groups.filter(name='Starfsmenn').exists():
        messages.error(request, _("Þú hefur ekki heimild til að hengja þig við verkefni."))
        return redirect('/')
    
    # Get the project page
    project_page = get_object_or_404(ProjectPage, id=page_id)
    
    # Update leidbeinendur for ALL language versions of this project
    all_language_versions = project_page.get_translations(inclusive=True)
    
    # Check if user is already assigned to this project
    if request.user in project_page.leidbeinendur.all():
        messages.warning(request, _("Þú ert nú þegar skráður sem leiðbeinandi fyrir þetta verkefni."))
    else:
        # Add current user as leidbeinandi to ALL language versions
        for lang_version in all_language_versions:
            lang_version.leidbeinendur.add(request.user)
            lang_version.save()
        
        messages.success(request, _("Þú hefur verið skráður sem leiðbeinandi fyrir þetta verkefni."))
    
    # Redirect back to the project page
    return redirect(project_page.url)


@login_required
@require_POST
@csrf_protect
def unregister_from_project(request, page_id):
    """
    Remove the current user (must be in Starfsmenn group) from a project as leidbeinandi
    """
    # Check if user is in Starfsmenn group
    if not request.user.groups.filter(name='Starfsmenn').exists():
        messages.error(request, _("Þú hefur ekki heimild til að draga þig úr verkefni."))
        return redirect('/')
    
    # Get the project page
    project_page = get_object_or_404(ProjectPage, id=page_id)
    
    # Update leidbeinendur for ALL language versions of this project
    all_language_versions = project_page.get_translations(inclusive=True)
    
    # Check if user is assigned to this project
    if request.user not in project_page.leidbeinendur.all():
        messages.warning(request, _("Þú ert ekki skráður sem leiðbeinandi fyrir þetta verkefni."))
    else:
        # Remove current user as leidbeinandi from ALL language versions
        for lang_version in all_language_versions:
            lang_version.leidbeinendur.remove(request.user)
            lang_version.save()
        
        messages.success(request, _("Þú hefur verið fjarlægður sem leiðbeinandi fyrir þetta verkefni."))
    
    # Redirect back to the project page
    return redirect(project_page.url)
