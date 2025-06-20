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
from .models import ProjectAd, ProjectPage, ProjectIndexPage, ProjectApplication, PendingProjectAd
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponseForbidden  # Add this import
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from people.models import PersonPage
from django.contrib.auth.models import User
from django.utils.translation import get_language
from base.models import Tag
import json
from django.db import models


def send_form_verification_email(contact_email, verification_code, company_name, title):
    """Send verification email for project advertisement form"""
    subject = 'Staðfestu verkefnaauglýsingu þína'
    
    # Create verification link
    verification_url = f"{settings.SITE_URL}/verify-project-ad/{verification_code}/"
    
    message = f"""
Halló!

Takk fyrir að senda inn verkefnaauglýsingu fyrir "{title}" frá {company_name}.

Til að ljúka við sendingu auglýsingarinnar, vinsamlegast staðfestu netfangið þitt með því að smella á tengilinn hér að neðan:

{verification_url}

Þessi tengill rennur út eftir 24 klukkustundir.

Ef þú sendir ekki inn þessa auglýsingu geturðu hunsað þennan tölvupóst.

Bestu kveðjur,
Háskóli Íslands
"""
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hi.is')
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            [contact_email],
            fail_silently=False,
        )
        print(f"Form verification email sent to {contact_email}")  # For debugging
    except Exception as e:
        print(f"Failed to send form verification email: {e}")  # For debugging


class AdvertiseView(FormView):
    template_name = "advertise/form.html"
    form_class    = ProjectAdForm
    success_url   = reverse_lazy("advertise:advertise-verification-sent")

    def form_valid(self, form):
        """Handle form submission and create pending advertisement"""
        
        # Get the form data
        form_data = form.cleaned_data.copy()
        
        # DEBUG: Check what's in the form data
        print(f"DEBUG: Form cleaned_data keys: {list(form_data.keys())}")
        print(f"DEBUG: Full form_data before processing: {form_data}")
        
        # Check specifically for tags
        if 'tags' in form_data:
            tags = form_data['tags']
            print(f"DEBUG: Tags in form_data: {tags}")
            print(f"DEBUG: Tags type: {type(tags)}")
            if hasattr(tags, '__iter__'):
                tag_ids = [tag.id if hasattr(tag, 'id') else tag for tag in tags]
                print(f"DEBUG: Tag IDs: {tag_ids}")
        else:
            print(f"DEBUG: ❌ No 'tags' key found in form_data")
        
        # Convert QuerySets to lists of IDs for JSON serialization
        if 'requested_advisors' in form_data:
            # Convert QuerySet to list of IDs
            advisor_ids = list(form_data['requested_advisors'].values_list('id', flat=True))
            form_data['requested_advisors'] = advisor_ids
            print(f"DEBUG: Converted advisors to IDs: {advisor_ids}")
        
        if 'tags' in form_data:
            # Convert QuerySet to list of IDs
            tag_ids = list(form_data['tags'].values_list('id', flat=True))
            form_data['tags'] = tag_ids
            print(f"DEBUG: Converted tags to IDs: {tag_ids}")
        
        # Convert date to string for JSON serialization
        if 'time_limit' in form_data and form_data['time_limit']:
            form_data['time_limit'] = form_data['time_limit'].strftime('%Y-%m-%d')
        
        # Extract contact email for separate storage
        contact_email = form_data['contact_email']
        
        print(f"DEBUG: Final form_data before saving: {form_data}")
        
        # Create pending project ad
        pending_ad = PendingProjectAd.objects.create(
            form_data=form_data,
            contact_email=contact_email
        )
        
        print(f"DEBUG: Created PendingProjectAd with ID: {pending_ad.id}")
        print(f"DEBUG: PendingProjectAd.form_data: {pending_ad.form_data}")
        
        # Send verification email
        self.send_verification_email(pending_ad)
        
        # Redirect to confirmation page - use the correct URL name
        return redirect('advertise:advertise-verification-sent')

    def send_verification_email(self, pending_ad):
        """Send verification email to the contact"""
        
        verification_url = self.request.build_absolute_uri(
            reverse('advertise:verify_project_ad', kwargs={
                'verification_code': pending_ad.verification_code
            })
        )
        
        subject = _('Staðfestið verkefnisauglýsingu ykkar')
        
        # Email content (you can customize this)
        message = _(
            'Halló!\n\n'
            'Þú hefur sent inn verkefnisauglýsingu með titlinum "{title}".\n\n'
            'Til að staðfesta auglýsinguna, vinsamlegast smelltu á eftirfarandi hlekk:\n'
            '{verification_url}\n\n'
            'Þessi hlekkur er gildur í 24 klukkustundir.\n\n'
            'Kveðja,\n'
            'Tölvunarfræðideild'
        ).format(
            title=pending_ad.form_data.get('title', 'Ótilgreindur titill'),
            verification_url=verification_url
        )
        
        # Send the email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[pending_ad.contact_email],
            fail_silently=False,
        )


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
        # Import here to avoid import issues
        from people.models import PersonPage
        
        # Find the person page by email
        person = PersonPage.objects.filter(email=email, live=True).first()
        
        if not person:
            print(f"DEBUG: No PersonPage found for email: {email}")
            return JsonResponse({'tags': []})
        
        print(f"DEBUG: Found PersonPage for {email}: {person.title}")
        
        # Get the tags for this person - check if tagged_items exists
        tags_data = []
        
        if hasattr(person, 'tagged_items'):
            tagged_items = person.tagged_items.all()
            print(f"DEBUG: Found {tagged_items.count()} tagged_items for {email}")
            
            for tagged_item in tagged_items:
                if hasattr(tagged_item, 'tag') and tagged_item.tag:
                    tags_data.append({
                        'id': tagged_item.tag.id,
                        'name': tagged_item.tag.name,
                        'color': tagged_item.tag.color
                    })
                    print(f"DEBUG: Added tag: {tagged_item.tag.name}")
        elif hasattr(person, 'tags'):
            # Alternative: direct tags relationship
            tags = person.tags.all()
            print(f"DEBUG: Found {tags.count()} direct tags for {email}")
            
            for tag in tags:
                tags_data.append({
                    'id': tag.id,
                    'name': tag.name,
                    'color': tag.color
                })
                print(f"DEBUG: Added tag: {tag.name}")
        else:
            print(f"DEBUG: No tags relationship found for PersonPage model")
        
        print(f"DEBUG: Returning {len(tags_data)} tags for {email}")
        return JsonResponse({'tags': tags_data})
        
    except ImportError as e:
        print(f"DEBUG: Import error - people.models.PersonPage not found: {e}")
        return JsonResponse({'error': 'PersonPage model not available', 'tags': []})
    except Exception as e:
        print(f"DEBUG: Error in advisor_tags_api for email {email}: {str(e)}")
        print(f"DEBUG: Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
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
    

class AdvertiseVerificationSentView(TemplateView):
    """Show confirmation that verification email was sent"""
    template_name = "advertise/verification_sent.html"


def verify_project_ad(request, verification_code):
    """Handle project advertisement verification"""
    from .models import PendingProjectAd
    
    try:
        pending_ad = get_object_or_404(PendingProjectAd, verification_code=verification_code)
        
        if pending_ad.is_expired():
            return render(request, 'advertise/verification_expired.html', {
                'contact_email': pending_ad.contact_email
            })
        
        if pending_ad.verified:
            return render(request, 'advertise/already_verified.html')
        
        # Mark as verified
        pending_ad.verified = True
        pending_ad.save()
        
        # Create the actual ProjectAd
        project_ad = pending_ad.create_project_ad()
        
        if project_ad:
            # Send notification email to admin (like the original code)
            advisors_list = ", ".join([
                advisor.get_full_name() or advisor.username 
                for advisor in project_ad.requested_advisors.all()
            ])
            
            send_mail(
                subject=f"Ný verkefnaauglýsing: {project_ad.title}",
                message=(
                    f"Fyrirtæki: {project_ad.company_name}\n"
                    f"Tengiliður: {project_ad.contact_name} <{project_ad.contact_email}>\n"
                    f"Tungumál: {project_ad.get_locale_display()}\n"
                    f"Óskir um leiðbeinendur: {advisors_list}\n\n"
                    f"Lýsing:\n{project_ad.description}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.PROJECT_AD_NOTIFY_TO],
            )
            
            print(f"DEBUG: Created ProjectAd with ID: {project_ad.id}")
            print(f"DEBUG: Notified admin at: {settings.PROJECT_AD_NOTIFY_TO}")
        
        return render(request, 'advertise/verification_success.html', {
            'project_ad': project_ad
        })
        
    except PendingProjectAd.DoesNotExist:
        return render(request, 'advertise/verification_invalid.html')


@require_GET
def tag_search_api(request):
    """API endpoint to search and return tags with localization"""
    query = request.GET.get('q', '').strip().lower()
    
    # Get all tags
    tags = Tag.objects.all().order_by('name_en')
    
    # Filter by search query if provided
    if query:
        tags = tags.filter(
            models.Q(name_en__icontains=query) | 
            models.Q(name_is__icontains=query)
        )
    
    # Get current language for proper name selection
    current_language = get_language()
    
    # Prepare response data
    tag_data = []
    for tag in tags:
        tag_data.append({
            'id': tag.id,
            'name': tag.get_localized_name(current_language),
            'name_en': tag.name_en,
            'name_is': tag.name_is,
            'color': tag.color,
        })
    
    return JsonResponse({
        'tags': tag_data,
        'count': len(tag_data)
    })

@require_GET 
def all_tags_api(request):
    """API endpoint to get all tags for initial load"""
    current_language = get_language()
    
    tags = Tag.objects.all().order_by('name_en')
    
    tag_data = []
    for tag in tags:
        tag_data.append({
            'id': tag.id,
            'name': tag.get_localized_name(current_language),
            'name_en': tag.name_en,
            'name_is': tag.name_is,
            'color': tag.color,
        })
    
    return JsonResponse({
        'tags': tag_data,
        'count': len(tag_data)
    })
