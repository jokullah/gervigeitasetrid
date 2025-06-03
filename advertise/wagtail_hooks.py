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

# Custom JavaScript to hide panels and add functionality
@hooks.register('insert_editor_js')
def add_custom_projectad_js():
    return mark_safe("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Check if we're on a ProjectAd edit page
        if (window.location.pathname.match(/\\/admin\\/projectad\\/edit\\/\\d+\\/$/) || 
            window.location.pathname.match(/\\/admin\\/projectad\\/create\\/$/)) {
            
            console.log('On ProjectAd page, customizing interface');
            
            // Extract the ID from the URL (if editing)
            const match = window.location.pathname.match(/\\/admin\\/projectad\\/edit\\/(\\d+)\\/$/);
            const projectAdId = match ? match[1] : null;
            
            // Wait a bit for Wagtail to render the page
            setTimeout(function() {
                // Debug: Find where panels should go
                console.log('DEBUG: Looking for sidebar elements...');
                const possibleSidebarSelectors = [
                    '.form-side',
                    '.edit-form__side',
                    '.w-form-side',
                    '[data-form-side]',
                    '.col-12.col-lg-4',
                    '.form-side__panel',
                    'aside',
                    '[role="complementary"]'
                ];
                
                let foundSidebar = false;
                possibleSidebarSelectors.forEach(selector => {
                    const element = document.querySelector(selector);
                    if (element) {
                        console.log(`Found potential sidebar: ${selector}`, element);
                        console.log(`  Classes: ${element.className}`);
                        console.log(`  Children: ${element.children.length}`);
                        foundSidebar = true;
                    }
                });
                
                if (!foundSidebar) {
                    console.log('No sidebar found. Looking for any panels...');
                    const anyPanels = document.querySelectorAll('.w-panel');
                    console.log(`Found ${anyPanels.length} panels total`);
                    anyPanels.forEach((panel, i) => {
                        console.log(`Panel ${i} parent:`, panel.parentElement.className);
                    });
                }
                
                // Find and hide ALL panels with unwanted titles
                const allPanels = document.querySelectorAll('.w-panel');
                allPanels.forEach(panel => {
                    const heading = panel.querySelector('.w-panel__heading');
                    if (heading) {
                        const text = heading.textContent.trim().toLowerCase();
                        console.log('Found panel with heading:', text);
                        // Hide panels with these specific texts
                        if (text.includes('í birtingu') || 
                            text.includes('notkun') || 
                            text.includes('status') || 
                            text.includes('usage') ||
                            text === 'status' ||
                            text === 'usage') {
                            panel.style.display = 'none';
                            console.log('Hid panel:', text);
                        }
                    }
                });
                
                // Also hide by data-side-panel attribute
                const statusPanel = document.querySelector('[data-side-panel="status"]');
                if (statusPanel) {
                    statusPanel.style.display = 'none';
                    console.log('Hid status panel by data attribute');
                }
                
                // Create and inject our custom panel
                if (projectAdId) {
                    // Try to find where other panels are located
                    const existingPanel = document.querySelector('.w-panel:not(#project-status-panel)');
                    let targetContainer = null;
                    
                    if (existingPanel && existingPanel.parentElement) {
                        targetContainer = existingPanel.parentElement;
                        console.log('Found panel container via existing panel:', targetContainer.className);
                    } else {
                        // Fallback to form-side
                        targetContainer = document.querySelector('.form-side');
                        console.log('Using fallback container: .form-side');
                    }
                    
                    if (targetContainer) {
                        // Remove any existing custom panel to avoid duplicates
                        const existingPanel = document.getElementById('project-status-panel');
                        if (existingPanel) {
                            existingPanel.remove();
                        }
                        
                        // Create custom panel HTML with proper Wagtail structure
                        const customPanel = document.createElement('section');
                        customPanel.className = 'w-panel';
                        customPanel.id = 'project-status-panel';
                        customPanel.setAttribute('aria-labelledby', 'panel-verkefnistada-heading');
                        
                        // Check if project exists
                        fetch('/admin/projectad/check-project/' + projectAdId + '/')
                            .then(response => response.json())
                            .then(data => {
                                if (data.exists) {
                                    customPanel.innerHTML = `
                                        <div class="w-panel__header">
                                            <h2 class="w-panel__heading" id="panel-verkefnistada-heading">
                                                <svg class="icon icon-folder-open-inverse w-panel__icon" aria-hidden="true">
                                                    <use href="#icon-folder-open-inverse"></use>
                                                </svg>
                                                Verkefnistaða
                                            </h2>
                                        </div>
                                        <div class="w-panel__content">
                                            <div class="w-field__wrapper" data-field-wrapper="">
                                                <div class="w-field__input" data-field-input="">
                                                    <p style="color: #007d40; font-weight: 600; margin-bottom: 12px;">
                                                        ✓ Verkefni hefur verið búið til
                                                    </p>
                                                    <a href="${data.edit_url}" 
                                                       class="button button-small button-secondary" 
                                                       style="width: 100%; text-align: center;">
                                                        Skoða verkefnasíðu
                                                    </a>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                } else {
                                    customPanel.innerHTML = `
                                        <div class="w-panel__header">
                                            <h2 class="w-panel__heading" id="panel-verkefnistada-heading">
                                                <svg class="icon icon-folder-open-inverse w-panel__icon" aria-hidden="true">
                                                    <use href="#icon-folder-open-inverse"></use>
                                                </svg>
                                                Verkefnistaða
                                            </h2>
                                        </div>
                                        <div class="w-panel__content">
                                            <div class="w-field__wrapper" data-field-wrapper="">
                                                <div class="w-field__input" data-field-input="">
                                                    <p style="color: #6c757d; margin: 0;">
                                                        Verkefni hefur ekki verið búið til
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    `;
                                }
                                
                                // Insert at the top of container
                                targetContainer.insertBefore(customPanel, targetContainer.firstChild);
                                console.log('Custom panel inserted in container:', targetContainer.className);
                            })
                            .catch(error => {
                                console.error('Error checking project status:', error);
                            });
                    } else {
                        console.warn('Could not find target container for panel');
                    }
                }
            }, 200); // Small delay to ensure DOM is ready
            
            // Add publish button functionality
            if (projectAdId) {
                // Find the form actions div
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
                
                if (!actionsDiv) {
                    const submitBtn = document.querySelector('button[type="submit"], input[type="submit"]');
                    if (submitBtn) {
                        actionsDiv = submitBtn.parentElement;
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
                                    
                                    // Get all form elements
                                    const allFormElements = document.querySelectorAll('input, textarea, select');
                                    
                                    // Filter for the actual data fields
                                    const dataFields = Array.from(allFormElements).filter(element => {
                                        const name = element.name;
                                        return name && (
                                            name.includes('title') || 
                                            name.includes('description') || 
                                            name.includes('company_name') || 
                                            name.includes('contact_name') || 
                                            name.includes('contact_email') || 
                                            name.includes('other')
                                        ) && name !== 'csrfmiddlewaretoken';
                                    });
                                    
                                    // Create a new form for our publish action
                                    const publishForm = document.createElement('form');
                                    publishForm.method = 'POST';
                                    publishForm.action = '/admin/projectad/publish/' + projectAdId + '/';
                                    
                                    // Copy the data fields
                                    dataFields.forEach(element => {
                                        const input = document.createElement('input');
                                        input.type = 'hidden';
                                        input.name = element.name;
                                        input.value = element.value;
                                        publishForm.appendChild(input);
                                    });
                                    
                                    // Add CSRF token
                                    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                                    if (csrfToken) {
                                        const csrfInput = document.createElement('input');
                                        csrfInput.type = 'hidden';
                                        csrfInput.name = 'csrfmiddlewaretoken';
                                        csrfInput.value = csrfToken.value;
                                        publishForm.appendChild(csrfInput);
                                    }
                                    
                                    document.body.appendChild(publishForm);
                                    publishForm.submit();
                                });
                                
                                actionsDiv.appendChild(publishBtn);
                            }
                        });
                }
            }
        }
    });
    </script>
    """)

# CSS to ensure proper styling and hide unwanted panels
@hooks.register('insert_editor_css')
def add_custom_projectad_css():
    return mark_safe("""
    <style>
    /* Hide default side panels for ProjectAd pages using multiple selectors */
    .model-projectad [data-side-panel="status"],
    .model-projectad .w-panel:has(.w-panel__heading:contains("í birtingu")),
    .model-projectad .w-panel:has(.w-panel__heading:contains("Notkun")),
    body[class*="projectad"] [data-side-panel="status"],
    body[class*="projectad"] .w-panel:has(.w-panel__heading:contains("Status")),
    body[class*="projectad"] .w-panel:has(.w-panel__heading:contains("Usage")) {
        display: none !important;
    }
    
    /* Force our custom panel to appear in the right column if it's in the wrong place */
    #project-status-panel {
        margin-bottom: 1.5rem;
    }
    
    /* If the panel ended up in the main content area, move it */
    .w-field__input #project-status-panel {
        position: fixed;
        right: 20px;
        top: 120px;
        width: 300px;
        z-index: 100;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Ensure proper panel styling */
    #project-status-panel .w-panel__header {
        background-color: #f5f5f5;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #e0e0e0;
    }
    
    #project-status-panel .w-panel__heading {
        margin: 0;
        font-size: 0.875rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    #project-status-panel .w-panel__icon {
        width: 1rem;
        height: 1rem;
    }
    
    #project-status-panel .w-panel__content {
        padding: 1rem;
    }
    
    #project-status-panel .button {
        display: block;
        text-decoration: none;
    }
    
    /* Try to find and style the proper sidebar location */
    .form-side #project-status-panel,
    .edit-form__side #project-status-panel,
    .col-lg-4 #project-status-panel {
        position: static;
        width: auto;
        box-shadow: none;
    }
    </style>
    """)
