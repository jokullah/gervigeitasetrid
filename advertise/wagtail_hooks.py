from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from wagtail import hooks
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.viewsets.base import ViewSetGroup
from .models import ProjectAd, ProjectPage, ProjectIndexPage

class ProjectAdViewSet(ModelViewSet):
    model = ProjectAd
    menu_label = _("Verkefnaauglýsingar")
    icon = "form"
    form_fields = [
        "title",
        "description",
        "company_name",
        "contact_name",
        "contact_email",
        "other",
    ]
    list_display = ("title", "company_name", "contact_email", "submitted_at")
    list_filter = ("company_name",)
    search_fields = ("title", "company_name", "contact_name")

class SubmissionAdminGroup(ViewSetGroup):
    menu_label = _("Hólf")
    menu_icon = "folder-open-inverse"
    items = (ProjectAdViewSet,)

@hooks.register("register_admin_viewset")
def register_submission_group():
    return SubmissionAdminGroup()

# Custom view to handle saving submission and creating project page
from django.views.generic import View
from django.forms.models import model_to_dict

class PublishProjectAdView(View):
    def post(self, request, pk):
        print(f"DEBUG: PublishProjectAdView called with pk={pk}")
        print(f"DEBUG: POST data keys: {list(request.POST.keys())}")
        print(f"DEBUG: POST data: {dict(request.POST)}")
        
        try:
            # Get the ProjectAd
            project_ad = get_object_or_404(ProjectAd, pk=pk)
            print(f"DEBUG: Found ProjectAd: {project_ad}")
            print(f"DEBUG: Original description: '{project_ad.description}'")
            
            # First, update the ProjectAd with any form data
            # Check for exact field names that Wagtail might be using
            updated_fields = []
            
            for key, value in request.POST.items():
                if key == 'title' or key.endswith('-title'):
                    project_ad.title = value
                    updated_fields.append(f"title: '{value}'")
                elif key == 'description' or key.endswith('-description'):
                    project_ad.description = value
                    updated_fields.append(f"description: '{value}'")
                elif key == 'company_name' or key.endswith('-company_name'):
                    project_ad.company_name = value
                    updated_fields.append(f"company_name: '{value}'")
                elif key == 'contact_name' or key.endswith('-contact_name'):
                    project_ad.contact_name = value
                    updated_fields.append(f"contact_name: '{value}'")
                elif key == 'contact_email' or key.endswith('-contact_email'):
                    project_ad.contact_email = value
                    updated_fields.append(f"contact_email: '{value}'")
                elif key == 'other' or key.endswith('-other'):
                    project_ad.other = value
                    updated_fields.append(f"other: '{value}'")
            
            print(f"DEBUG: Updated fields: {updated_fields}")
            
            project_ad.save()
            print(f"DEBUG: ProjectAd updated and saved")
            print(f"DEBUG: New description: '{project_ad.description}'")
            
            # Check if a project page already exists for this ad
            if project_ad.project_page:
                print(f"DEBUG: Found existing project page: {project_ad.project_page}")
                messages.info(
                    request,
                    f"Project page already exists for '{project_ad.title}'. Redirecting to edit page."
                )
                edit_url = reverse('wagtailadmin_pages:edit', args=[project_ad.project_page.id])
                return HttpResponseRedirect(edit_url)
            
            # Find ProjectIndexPage
            project_index = ProjectIndexPage.objects.first()
            
            if not project_index:
                messages.error(
                    request,
                    "No Project Index Page found. Please create one first in Pages → Add child page."
                )
                return HttpResponseRedirect(reverse('wagtailadmin_projectad_modeladmin:edit', args=[pk]))
            
            print(f"DEBUG: Found ProjectIndexPage: {project_index}")
            
            # Create the ProjectPage with pre-filled data
            project_page = ProjectPage(
                title=project_ad.title,
                description=project_ad.description,
                company_name=project_ad.company_name,
                contact_name=project_ad.contact_name,
                contact_email=project_ad.contact_email,
                other=project_ad.other or "",
                live=False,  # Start as draft/unpublished
                show_in_menus=False,
            )
            
            print(f"DEBUG: Created ProjectPage instance: {project_page}")
            
            # Add as child of ProjectIndexPage
            project_index.add_child(instance=project_page)
            print(f"DEBUG: Added as child, ProjectPage ID: {project_page.id}")
            
            # Link the ProjectAd to the newly created ProjectPage
            project_ad.project_page = project_page
            project_ad.save()
            print(f"DEBUG: Linked ProjectAd to ProjectPage")
            
            messages.success(
                request,
                f"Project page created for '{project_ad.title}'. You can now edit and publish it."
            )
            
            # Redirect to the Wagtail page editor for the newly created page
            edit_url = reverse('wagtailadmin_pages:edit', args=[project_page.id])
            print(f"DEBUG: Redirecting to: {edit_url}")
            return HttpResponseRedirect(edit_url)
            
        except Exception as e:
            print(f"DEBUG: Error occurred: {e}")
            import traceback
            traceback.print_exc()
            messages.error(
                request,
                f"Error creating project page: {str(e)}"
            )
            return HttpResponseRedirect(reverse('wagtailadmin_projectad_modeladmin:edit', args=[pk]))

# View to check if a project page exists for this ad
class CheckProjectPageView(View):
    def get(self, request, pk):
        try:
            project_ad = get_object_or_404(ProjectAd, pk=pk)
            
            # Check if project page exists
            if project_ad.project_page:
                return JsonResponse({
                    'exists': True,
                    'project_id': project_ad.project_page.id,
                    'edit_url': reverse('wagtailadmin_pages:edit', args=[project_ad.project_page.id])
                })
            else:
                return JsonResponse({'exists': False})
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

# Register custom URLs
@hooks.register('register_admin_urls')
def register_publish_project_ad_url():
    return [
        path('projectad/publish/<int:pk>/', PublishProjectAdView.as_view(), name='publish_project_ad'),
        path('projectad/check-project/<int:pk>/', CheckProjectPageView.as_view(), name='check_project_page'),
    ]

# Add the custom buttons
@hooks.register('insert_editor_js')
def add_publish_button_js():
    return mark_safe("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Check if we're on a ProjectAd edit page by looking for the specific URL pattern
        if (window.location.pathname.match(/\\/admin\\/projectad\\/edit\\/\\d+\\/$/)) {
            console.log('On ProjectAd edit page, adding publish button');
            
            // Extract the ID from the URL
            const match = window.location.pathname.match(/\\/admin\\/projectad\\/edit\\/(\\d+)\\/$/);
            const projectAdId = match ? match[1] : null;
            
            if (!projectAdId) {
                console.log('Could not extract ProjectAd ID from URL');
                return;
            }
            
            // Find the form actions div (where the save button lives)
            const possibleSelectors = [
                '.object-detail__actions',
                '.actions', 
                'form .button-row',
                '.form-side__actions',
                '.footer-actions',
                'footer .actions',
                '[data-edit-form] footer'
            ];
            
            let actionsDiv = null;
            for (let selector of possibleSelectors) {
                actionsDiv = document.querySelector(selector);
                if (actionsDiv) {
                    console.log('Found actions div with selector:', selector);
                    break;
                }
            }
            
            // If still not found, try to find any element containing a submit button
            if (!actionsDiv) {
                const submitBtn = document.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) {
                    actionsDiv = submitBtn.parentElement;
                    console.log('Found actions div via submit button parent');
                }
            }
            
            if (actionsDiv) {
                // Check if project page already exists
                fetch('/admin/projectad/check-project/' + projectAdId + '/')
                    .then(response => response.json())
                    .then(data => {
                        if (data.exists) {
                            // Create "Skoða verkefni" button
                            const viewBtn = document.createElement('a');
                            viewBtn.href = data.edit_url;
                            viewBtn.className = 'button button-secondary';
                            viewBtn.style.marginLeft = '10px';
                            viewBtn.innerHTML = '✓ Skoða verkefni';
                            viewBtn.title = 'Verkefnasíða hefur þegar verið búin til úr þessari auglýsingu';
                            actionsDiv.appendChild(viewBtn);
                            console.log('View project button added');
                        } else {
                            // Create "Birta verkefni" button
                            const publishBtn = document.createElement('a');
                            publishBtn.href = '#';
                            publishBtn.className = 'button button-primary';
                            publishBtn.style.marginLeft = '10px';
                            publishBtn.innerHTML = '📝 Birta verkefni';
                            
                            publishBtn.addEventListener('click', function(e) {
                                e.preventDefault();
                                
                                if (!confirm('Ertu viss um að þú viljir búa til verkefnasíðu úr þessari auglýsingu?')) {
                                    return false;
                                }
                                
                                // Get all forms on the page (Wagtail might have multiple forms)
                                const forms = document.querySelectorAll('form');
                                console.log('Forms found:', forms.length);
                                
                                // Get all form inputs, textareas, and selects from all forms
                                const allFormElements = document.querySelectorAll('input, textarea, select');
                                console.log('All form elements found:', allFormElements.length);
                                
                                // Filter for the actual data fields (exclude search, pagination, etc.)
                                const dataFields = Array.from(allFormElements).filter(element => {
                                    const name = element.name;
                                    const id = element.id;
                                    console.log('Checking element:', {name, id, type: element.type, value: element.value});
                                    
                                    // Include fields that look like our model fields
                                    return name && (
                                        name.includes('title') || 
                                        name.includes('description') || 
                                        name.includes('company_name') || 
                                        name.includes('contact_name') || 
                                        name.includes('contact_email') || 
                                        name.includes('other') ||
                                        name === 'title' ||
                                        name === 'description' ||
                                        name === 'company_name' ||
                                        name === 'contact_name' ||
                                        name === 'contact_email' ||
                                        name === 'other'
                                    ) && name !== 'csrfmiddlewaretoken';
                                });
                                
                                console.log('Data fields found:', dataFields.length);
                                
                                // Create a new form for our publish action
                                const publishForm = document.createElement('form');
                                publishForm.method = 'POST';
                                publishForm.action = '/admin/projectad/publish/' + projectAdId + '/';
                                
                                // Copy the data fields to our publish form
                                dataFields.forEach(element => {
                                    console.log('Copying field:', element.name, '=', element.value);
                                    const input = document.createElement('input');
                                    input.type = 'hidden';
                                    input.name = element.name;
                                    input.value = element.value;
                                    publishForm.appendChild(input);
                                });
                                
                                // IMPORTANT: Add CSRF token
                                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                                if (csrfToken) {
                                    const csrfInput = document.createElement('input');
                                    csrfInput.type = 'hidden';
                                    csrfInput.name = 'csrfmiddlewaretoken';
                                    csrfInput.value = csrfToken.value;
                                    publishForm.appendChild(csrfInput);
                                    console.log('CSRF token added');
                                } else {
                                    console.error('CSRF token not found!');
                                    alert('CSRF token not found. Please refresh the page and try again.');
                                    return;
                                }
                                
                                console.log('About to submit form with action:', publishForm.action);
                                document.body.appendChild(publishForm);
                                publishForm.submit();
                            });
                            
                            actionsDiv.appendChild(publishBtn);
                            console.log('Publish button added successfully');
                        }
                    })
                    .catch(error => {
                        console.error('Error checking for existing project:', error);
                        // Fallback: show publish button
                        const publishBtn = document.createElement('a');
                        publishBtn.href = '#';
                        publishBtn.className = 'button button-primary';
                        publishBtn.style.marginLeft = '10px';
                        publishBtn.innerHTML = '📝 Birta verkefni';
                        actionsDiv.appendChild(publishBtn);
                    });
            } else {
                console.log('Could not find actions div to add button');
            }
        }
    });
    </script>
    """)
