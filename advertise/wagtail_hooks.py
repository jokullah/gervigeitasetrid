from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from wagtail import hooks
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.viewsets.base import ViewSetGroup
from wagtail.models import Locale
from .models import ProjectAd, ProjectPage, ProjectIndexPage
from wagtail.admin.ui.tables import Column
from django.utils.html import format_html


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
        "locale",
    ]
    
    # Back to simple list_display
    list_display = ("title", "company_name", "contact_email", "locale_display", "status_display", "submitted_at")
    list_filter = ("company_name", "locale", "viewed_at")
    search_fields = ("title", "company_name", "contact_name")
    
    edit_template_name = 'advertise/admin/projectad_edit.html'
    index_template_name = 'advertise/admin/projectad_list.html'  # Add this line
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project_page')


class SubmissionAdminGroup(ViewSetGroup):
    menu_label = _("Hólf")
    menu_icon = "folder-open-inverse"
    items = (ProjectAdViewSet,)

@hooks.register("register_admin_viewset")
def register_submission_group():
    return SubmissionAdminGroup()


# Middleware-like hook to mark ads as viewed when accessed
@hooks.register('before_edit_page')
def mark_project_ad_as_viewed(request, page):
    """Mark ProjectAd as viewed when the edit page is accessed"""
    pass  # This hook is for Wagtail pages, not our custom model


# Custom hook for our model editing
@hooks.register('after_edit_page')  
def mark_ad_viewed_after_edit(request, page):
    """This won't work for our custom model, we need a different approach"""
    pass


# Better approach: Use a custom view mixin
from django.views.generic.edit import UpdateView

class ProjectAdEditView(UpdateView):
    """Custom edit view that marks ads as viewed"""
    model = ProjectAd
    fields = [
        "title",
        "description", 
        "company_name",
        "contact_name",
        "contact_email",
        "other",
        "locale",
    ]
    template_name = 'advertise/admin/projectad_edit.html'
    
    def get_object(self, queryset=None):
        """Mark as viewed when object is retrieved for editing"""
        obj = super().get_object(queryset)
        if obj and obj.is_new:
            obj.mark_as_viewed()
            print(f"DEBUG: Marked ad '{obj.title}' as viewed")
        return obj
    
    def get_success_url(self):
        return reverse('wagtailadmin_projectad_modeladmin:index')


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
            print(f"DEBUG: ProjectAd locale: {project_ad.locale}")
            
            # Mark as viewed since admin is interacting with it
            if project_ad.is_new:
                project_ad.mark_as_viewed()
                print(f"DEBUG: Marked ad as viewed during publish")
            
            # Update the ProjectAd with any form data
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
                elif key == 'locale' or key.endswith('-locale'):
                    project_ad.locale = value
                    updated_fields.append(f"locale: '{value}'")
            
            print(f"DEBUG: Updated fields: {updated_fields}")
            
            project_ad.save()
            print(f"DEBUG: ProjectAd updated and saved")
            
            # Check if a project page already exists for this ad
            if project_ad.project_page:
                print(f"DEBUG: Found existing project page: {project_ad.project_page}")
                messages.info(
                    request,
                    f"Project page already exists for '{project_ad.title}'. Redirecting to edit page."
                )
                edit_url = reverse('wagtailadmin_pages:edit', args=[project_ad.project_page.id])
                return HttpResponseRedirect(edit_url)
            
            # Get the correct Wagtail locale object
            try:
                wagtail_locale = Locale.objects.get(language_code=project_ad.locale)
                print(f"DEBUG: Found Wagtail locale: {wagtail_locale}")
            except Locale.DoesNotExist:
                print(f"DEBUG: Locale {project_ad.locale} not found, falling back to default")
                wagtail_locale = Locale.get_default()
            
            # Find ProjectIndexPage in the correct locale
            try:
                project_index = ProjectIndexPage.objects.filter(locale=wagtail_locale).first()
                if not project_index:
                    # Fallback to any ProjectIndexPage
                    project_index = ProjectIndexPage.objects.first()
                    print(f"DEBUG: No ProjectIndexPage found for locale {wagtail_locale}, using fallback")
            except:
                project_index = ProjectIndexPage.objects.first()
            
            if not project_index:
                messages.error(
                    request,
                    "No Project Index Page found. Please create one first in Pages → Add child page."
                )
                return HttpResponseRedirect(reverse('wagtailadmin_projectad_modeladmin:edit', args=[pk]))
            
            print(f"DEBUG: Found ProjectIndexPage: {project_index} (locale: {project_index.locale})")
            
            # Create the ProjectPage with pre-filled data in the correct locale
            project_page = ProjectPage(
                title=project_ad.title,
                description=project_ad.description,
                company_name=project_ad.company_name,
                contact_name=project_ad.contact_name,
                contact_email=project_ad.contact_email,
                other=project_ad.other or "",
                live=False,  # Start as draft/unpublished
                show_in_menus=False,
                locale=wagtail_locale,  # Set the correct locale
            )
            
            print(f"DEBUG: Created ProjectPage instance: {project_page} (locale: {wagtail_locale})")
            
            # Add as child of ProjectIndexPage
            project_index.add_child(instance=project_page)
            print(f"DEBUG: Added as child, ProjectPage ID: {project_page.id}")
            
            # Link the ProjectAd to the newly created ProjectPage
            project_ad.project_page = project_page
            project_ad.save()
            print(f"DEBUG: Linked ProjectAd to ProjectPage")
            
            messages.success(
                request,
                f"Project page created for '{project_ad.title}' in {wagtail_locale.get_display_name()}. You can now edit and publish it."
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
            
            # Mark as viewed when checking (since admin is looking at it)
            if project_ad.is_new:
                project_ad.mark_as_viewed()
                print(f"DEBUG: Marked ad '{project_ad.title}' as viewed during check")
            
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


# Custom view that marks ads as viewed when accessed via the admin
class MarkAsViewedView(View):
    def post(self, request, pk):
        """Endpoint to mark a specific ad as viewed"""
        try:
            project_ad = get_object_or_404(ProjectAd, pk=pk)
            if project_ad.is_new:
                project_ad.mark_as_viewed()
                print(f"DEBUG: Manually marked ad '{project_ad.title}' as viewed")
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# New endpoint to mark multiple ads as viewed at once
class MarkAllViewedView(View):
    def post(self, request):
        """Endpoint to mark multiple ads as viewed"""
        try:
            import json
            data = json.loads(request.body)
            ad_ids = data.get('ad_ids', [])
            
            if ad_ids:
                from django.utils import timezone
                updated_count = ProjectAd.objects.filter(
                    id__in=ad_ids, 
                    viewed_at__isnull=True
                ).update(viewed_at=timezone.now())
                
                print(f"DEBUG: Marked {updated_count} ads as viewed via batch update")
                return JsonResponse({'success': True, 'count': updated_count})
            else:
                return JsonResponse({'success': True, 'count': 0})
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# Register custom URLs
@hooks.register('register_admin_urls')
def register_publish_project_ad_url():
    return [
        path('projectad/publish/<int:pk>/', PublishProjectAdView.as_view(), name='publish_project_ad'),
        path('projectad/check-project/<int:pk>/', CheckProjectPageView.as_view(), name='check_project_page'),
        path('projectad/mark-viewed/<int:pk>/', MarkAsViewedView.as_view(), name='mark_project_ad_viewed'),
        path('projectad/get-new-ads/', GetNewAdsView.as_view(), name='get_new_ads'),
        path('projectad/mark-all-viewed/', MarkAllViewedView.as_view(), name='mark_all_project_ads_viewed'),
    ]


# Custom JavaScript to add button functionality and mark ads as viewed
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
            
            // Mark as viewed when page loads (if editing existing ad)
            if (projectAdId) {
                fetch('/admin/projectad/mark-viewed/' + projectAdId + '/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'Content-Type': 'application/json',
                    }
                }).then(response => response.json())
                  .then(data => {
                      if (data.success) {
                          console.log('Marked ad as viewed');
                      }
                  }).catch(err => console.log('Error marking as viewed:', err));
            }
            
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
                                            name.includes('other') ||
                                            name.includes('locale')
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
        
        // Add NEW badges to the ProjectAd list page
        if (window.location.pathname.match(/\\/admin\\/projectad\\/$/)) {
            console.log('On ProjectAd list page - adding NEW indicators');
            
            // Wait a bit for the page to fully load
            setTimeout(function() {
                addNewIndicators();
            }, 100);
            
            // Also add indicators after any AJAX updates
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        addNewIndicators();
                    }
                });
            });
            
            const tableContainer = document.querySelector('.listing, .w-table, table');
            if (tableContainer) {
                observer.observe(tableContainer, { childList: true, subtree: true });
            }
        }
    });
    
    function addNewIndicators() {
        // Get all new ads info from the server
        fetch('/admin/projectad/get-new-ads/')
            .then(response => response.json())
            .then(data => {
                if (data.new_ad_ids && data.new_ad_ids.length > 0) {
                    console.log('Found new ads:', data.new_ad_ids);
                    
                    // Find all table rows and add NEW badges
                    const tableRows = document.querySelectorAll('tbody tr, .listing tbody tr, .w-table tbody tr');
                    
                    tableRows.forEach(row => {
                        // Look for edit link to extract the ID
                        const editLink = row.querySelector('a[href*="/edit/"]');
                        if (editLink) {
                            const match = editLink.href.match(/\\/edit\\/(\\d+)\\//);
                            if (match) {
                                const adId = parseInt(match[1]);
                                
                                if (data.new_ad_ids.includes(adId)) {
                                    // Remove any existing NEW badge
                                    const existingBadge = row.querySelector('.new-ad-badge');
                                    if (existingBadge) {
                                        existingBadge.remove();
                                    }
                                    
                                    // Find the title cell (usually first td or the one with the edit link)
                                    const titleCell = editLink.closest('td');
                                    if (titleCell && !titleCell.querySelector('.new-ad-badge')) {
                                        const newBadge = document.createElement('span');
                                        newBadge.className = 'new-ad-badge';
                                        newBadge.innerHTML = 'NEW';
                                        newBadge.style.cssText = `
                                            background: #ff6b6b;
                                            color: white;
                                            padding: 2px 6px;
                                            border-radius: 10px;
                                            font-size: 10px;
                                            font-weight: bold;
                                            margin-left: 8px;
                                            display: inline-block;
                                            vertical-align: middle;
                                            animation: pulse 2s infinite;
                                        `;
                                        
                                        titleCell.appendChild(newBadge);
                                    }
                                }
                            }
                        }
                    });
                    
                    // Add CSS animation if not already added
                    if (!document.querySelector('#new-badge-styles')) {
                        const style = document.createElement('style');
                        style.id = 'new-badge-styles';
                        style.textContent = `
                            @keyframes pulse {
                                0% { opacity: 1; transform: scale(1); }
                                50% { opacity: 0.8; transform: scale(1.05); }
                                100% { opacity: 1; transform: scale(1); }
                            }
                        `;
                        document.head.appendChild(style);
                    }
                }
            })
            .catch(err => console.log('Error fetching new ads:', err));
    }
    </script>
    """)


# New endpoint to get list of new ad IDs
class GetNewAdsView(View):
    def get(self, request):
        """Return IDs of all new (unviewed) ads"""
        try:
            new_ad_ids = list(ProjectAd.objects.filter(viewed_at__isnull=True).values_list('id', flat=True))
            return JsonResponse({'new_ad_ids': new_ad_ids})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


from wagtail.admin.ui.components import Component

class NewAdsBanner(Component):
    name = "new-ads-banner"
    order = -1  # Show before other panels (negative number = higher priority)
    
    def render_html(self, parent_context):
        """Render the new ads banner if there are unviewed ads"""
        
        # Count new (unviewed) ads
        new_ads_count = ProjectAd.objects.filter(viewed_at__isnull=True).count()
        
        if new_ads_count == 0:
            return ""
        
        # Create the message
        if new_ads_count == 1:
            message = _("1 new project advertisement")
        else:
            message = _("{count} new project advertisements").format(count=new_ads_count)
        
        # Use direct URL to ads list
        ads_url = '/admin/projectad/'
        
        return mark_safe(f"""
            <div id="new-ads-banner" style="
                background: linear-gradient(135deg, #ff6b6b, #ee5a24);
                color: white;
                padding: 15px 20px;
                margin: 0 0 20px 0;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3);
                border-left: 5px solid #fff;
                position: relative;
                overflow: hidden;
            ">
                <div style="
                    background: rgba(255,255,255,0.1);
                    position: absolute;
                    top: 0;
                    right: 0;
                    bottom: 0;
                    width: 60px;
                    transform: skewX(-10deg);
                    margin-right: -20px;
                "></div>
                <div style="position: relative; z-index: 1;">
                    <h3 style="margin: 0 0 8px 0; font-size: 18px;">
                        🔔 {message}
                    </h3>
                    <p style="margin: 0 0 12px 0; opacity: 0.9; font-size: 14px;">
                        {_("New project advertisements are waiting for review")}
                    </p>
                    <a href="{ads_url}" style="
                        background: rgba(255,255,255,0.2);
                        color: white;
                        padding: 8px 16px;
                        border-radius: 20px;
                        text-decoration: none;
                        font-weight: bold;
                        font-size: 14px;
                        border: 1px solid rgba(255,255,255,0.3);
                        transition: all 0.3s ease;
                    " onmouseover="this.style.background='rgba(255,255,255,0.3)'"
                       onmouseout="this.style.background='rgba(255,255,255,0.2)'">
                        {_("View advertisements")} →
                    </a>
                </div>
            </div>
        """)

@hooks.register('construct_homepage_panels')
def add_new_ads_banner(request, panels):
    """Add a banner for new project ads on the admin home page"""
    panels.append(NewAdsBanner())


# JavaScript to hide banner after visiting ads (add to admin base template or here)
@hooks.register('insert_editor_js')
def add_banner_hide_js():
    return mark_safe("""
    <script>
    // Hide the new ads banner after visiting the ads list
    document.addEventListener('DOMContentLoaded', function() {
        if (window.location.pathname.match(/\\/admin\\/projectad\\/$/)) {
            // We're on the ads list page, schedule banner refresh on homepage
            sessionStorage.setItem('visited_ads_list', 'true');
        }
        
        // If we're on homepage and user visited ads list, try to hide banner
        if (window.location.pathname === '/admin/' && sessionStorage.getItem('visited_ads_list')) {
            sessionStorage.removeItem('visited_ads_list');
            
            // Small delay to let the page load, then refresh if banner is still there
            setTimeout(function() {
                const banner = document.getElementById('new-ads-banner');
                if (banner) {
                    // Force a page refresh to update the banner count
                    window.location.reload();
                }
            }, 500);
        }
    });
    </script>
    """)
