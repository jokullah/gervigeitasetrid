from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.core.mail import send_mail
from django.conf import settings
from django.utils import translation  # ADD THIS IMPORT
from .forms import ProjectAdForm, ProjectApplicationForm  # Add ProjectApplicationForm import
from wagtail.models import Page
from django.shortcuts import get_object_or_404, redirect, render  # Add render import
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import ProjectAd, ProjectPage, ProjectIndexPage, ProjectApplication  # Add ProjectApplication import
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseForbidden  # Add this import
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from people.models import PersonPage
from django.contrib.auth.models import User


class AdvertiseView(FormView):
    template_name = "advertise/form.html"
    form_class    = ProjectAdForm
    success_url   = reverse_lazy("advertise:advertise-thanks")

    def form_valid(self, form):
        # CRITICAL: Don't save yet - we need to set locale first
        instance = form.save(commit=False)
        
        # Capture the current language from the request
        current_language = translation.get_language()
        instance.locale = current_language
        
        # Now save the instance first (required before saving many-to-many)
        instance.save()
        
        # IMPORTANT: Save the many-to-many data (including requested_advisors)
        form.save_m2m()
        
        # Debug logging
        print(f"DEBUG: Form submitted from {self.request.path}")
        print(f"DEBUG: Current language: {current_language}")
        print(f"DEBUG: Saved ProjectAd with locale: {instance.locale}")
        print(f"DEBUG: Requested advisors count: {instance.requested_advisors.count()}")
        for advisor in instance.requested_advisors.all():
            print(f"DEBUG: - {advisor.get_full_name()} ({advisor.email})")
        
        # Send notification email
        advisors_list = ", ".join([
            advisor.get_full_name() or advisor.username 
            for advisor in instance.requested_advisors.all()
        ])
        
        send_mail(
            subject=f"Ný verkefnaauglýsing: {instance.title}",
            message=(
                f"Fyrirtæki: {instance.company_name}\n"
                f"Tengiliður: {instance.contact_name} <{instance.contact_email}>\n"
                f"Tungumál: {instance.get_locale_display()}\n"
                f"Óskir um leiðbeinendur: {advisors_list}\n\n"
                f"Lýsing:\n{instance.description}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.PROJECT_AD_NOTIFY_TO],
        )
        
        return super().form_valid(form)


class AdvertiseThanksView(TemplateView):
    template_name = "advertise/thanks.html"


@login_required
def apply_to_project(request, page_id):
    """View for students to apply to a project"""
    project_page = get_object_or_404(ProjectPage, id=page_id)
    
    # Check if user is a student
    if not request.user.groups.filter(name='Nemandi').exists():
        return HttpResponseForbidden(_("Aðeins nemendur geta sótt um verkefni"))
    
    # Check if user has already applied
    existing_application = ProjectApplication.objects.filter(
        project_page=project_page,
        applicant=request.user
    ).first()
    
    if existing_application:
        messages.info(request, _("Þú hefur þegar sótt um þetta verkefni"))
        return redirect(project_page.url)
    
    if request.method == 'POST':
        form = ProjectApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.project_page = project_page
            application.applicant = request.user
            application.save()
            
            messages.success(request, _("Umsókn þín hefur verið send!"))
            return redirect(project_page.url)
    else:
        form = ProjectApplicationForm()
    
    context = {
        'form': form,
        'project_page': project_page,
        'page': project_page,  # For template compatibility
    }
    
    return render(request, 'advertise/apply_to_project.html', context)


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

@require_GET
def advisor_tags_api(request):
    """API endpoint to fetch tags for an advisor by email"""
    email = request.GET.get('email')
    
    if not email:
        return JsonResponse({'error': 'Email parameter required'}, status=400)
    
    try:
        # Find the person page by email
        person = PersonPage.objects.filter(email=email, live=True).first()
        
        if not person:
            return JsonResponse({'tags': []})
        
        # Get the tags for this person
        tags_data = []
        for tag in person.tags.all():
            tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color
            })
        
        return JsonResponse({'tags': tags_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def user_email_api(request):
    """API endpoint to get user email by user ID"""
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return JsonResponse({'error': 'User ID parameter required'}, status=400)
    
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({'email': user.email})
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
