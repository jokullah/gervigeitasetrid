from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from django.utils.translation import gettext_lazy as _
from wagtail.search.index import SearchField
from django.contrib.auth.models import User
from django import forms
from wagtail.admin.forms import WagtailAdminPageForm
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe


class ProjectPageForm(WagtailAdminPageForm):
    """Custom form ONLY for ProjectPage with enhanced advisor field styling"""
    
    class Media:
        css = {
            'all': ('advertise/css/projectpage_clean.css',)
        }
        js = ('advertise/js/projectpage_clean.js',)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only apply if this is actually a ProjectPage form
        # Check if the instance is a ProjectPage
        instance = kwargs.get('instance')
        if instance and hasattr(instance, '__class__'):
            if 'ProjectPage' not in instance.__class__.__name__:
                return  # Don't apply customizations to other page types
        
        # Get the staff members queryset
        staff_queryset = User.objects.filter(
            groups__name='Starfsmenn'
        ).order_by('first_name', 'last_name')
        
        # Get the students queryset
        student_queryset = User.objects.filter(
            groups__name='Nemandi'
        ).order_by('first_name', 'last_name')
        
        # Force checkbox widgets for advisor fields
        if 'requested_advisors' in self.fields:
            self.fields['requested_advisors'].widget = forms.CheckboxSelectMultiple(
                attrs={
                    'class': 'projectpage-advisor-checkboxes projectpage-requested-advisors',
                    'data-field': 'requested_advisors'
                }
            )
            self.fields['requested_advisors'].queryset = staff_queryset
            
            # Override the choices to display full names
            self.fields['requested_advisors'].choices = [
                (user.pk, user.get_full_name() if user.get_full_name().strip() else user.username)
                for user in staff_queryset
            ]
            
        if 'leidbeinendur' in self.fields:
            self.fields['leidbeinendur'].widget = forms.CheckboxSelectMultiple(
                attrs={
                    'class': 'projectpage-advisor-checkboxes projectpage-leidbeinendur-advisors',
                    'data-field': 'leidbeinendur'
                }
            )
            self.fields['leidbeinendur'].queryset = staff_queryset
            
            # Override the choices to display full names
            self.fields['leidbeinendur'].choices = [
                (user.pk, user.get_full_name() if user.get_full_name().strip() else user.username)
                for user in staff_queryset
            ]
        
        # Apply checkbox styling to selected_students field
        if 'selected_students' in self.fields:
            self.fields['selected_students'].widget = forms.CheckboxSelectMultiple(
                attrs={
                    'class': 'projectpage-advisor-checkboxes projectpage-selected-students',
                    'data-field': 'selected_students'
                }
            )
            self.fields['selected_students'].queryset = student_queryset
            
            # Override the choices to display full names
            self.fields['selected_students'].choices = [
                (user.pk, user.get_full_name() if user.get_full_name().strip() else user.username)
                for user in student_queryset
            ]


class ProjectAd(models.Model):
    title          = models.CharField(_("Titill"), max_length=200) 
    description    = models.TextField(_("Lýsing")) 
    company_name   = models.CharField(_("Fyrirtæki"), max_length=200) 
    contact_name   = models.CharField(_("Tengiliður"), max_length=120) 
    contact_email  = models.EmailField(_("Tengiliðapóstur")) 
    other          = models.TextField(_("Annað"), blank=True) 
    submitted_at   = models.DateTimeField(auto_now_add=True)
    
    # NEW: Funding fields
    is_funded      = models.BooleanField(_("Fjármagnað verkefni"), default=False, help_text=_("Krossa við ef verkefnið er fjármagnað"))
    funding_amount = models.PositiveIntegerField(_("Fjárhæð (ISK)"), null=True, blank=True, help_text=_("Heildarfjárhæð verkefnisins í íslenskum krónum"))
    
    # NEW: Requested advisors
    requested_advisors = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Óskir um leiðbeinendur"),
        help_text=_("Veljið starfsmenn sem þið viljið helst fá sem leiðbeinendur"),
        limit_choices_to={'groups__name': 'Starfsmenn'},
        related_name='requested_projects'
    )
    
    # Track if admin has viewed this ad
    viewed_at      = models.DateTimeField(null=True, blank=True, verbose_name=_("Viewed at"))
    
    locale = models.CharField(
        _("Tungumál"),
        max_length=10,
        choices=[
            ('is', _('Icelandic')),  
            ('en', _('English')),  
        ],
        default='is',
        help_text=_("Tungumál auglýsingar þegar hún er birt")
    )
    
    project_page   = models.ForeignKey(
        'advertise.ProjectPage', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Linked project page"),
        help_text=_("Project page created from this advertisement")
    )
    
    class Meta:
        verbose_name        = _("Project advertisement")
        verbose_name_plural = _("Project advertisements")
        ordering            = ["-submitted_at"]
    
    def __str__(self):
        return f"{self.title} ({self.company_name})"
    
    @property
    def is_new(self):
        """Check if this ad is new (not viewed by admin yet)"""
        return self.viewed_at is None
    
    @property
    def has_project_page(self):
        """Check if this ad has been converted to a project page (including translations)"""
        return self.get_project_page() is not None
    
    def get_project_page(self):
        """Get the project page for this ad, checking translations if original is deleted"""
        print(f"DEBUG: get_project_page() called for ad '{self.title}'")
        print(f"DEBUG: self.project_page: {self.project_page}")
        
        # First check direct link - accept both live AND draft pages
        if self.project_page:
            print(f"DEBUG: Direct project_page exists, checking if live: {self.project_page.live}")
            # Accept the page whether it's live or draft
            print(f"DEBUG: Direct project_page exists, returning it (live or draft)")
            return self.project_page
        
        # Look for translations if original page exists
        if self.project_page:
            print(f"DEBUG: Direct project_page exists, checking translations")
            try:
                translations = self.project_page.get_translations()
                print(f"DEBUG: Found {len(translations)} translations")
                # Find any translation (live or draft)
                for translation in translations:
                    print(f"DEBUG: Checking translation {translation.id}, live: {translation.live}")
                    # Return first translation found (live or draft)
                    print(f"DEBUG: Found translation, updating link and returning")
                    self.project_page = translation
                    self.save(update_fields=['project_page'])
                    return translation
            except Exception as e:
                print(f"DEBUG: Error getting translations: {e}")
                pass
        
        # Fallback: search by content matching - include drafts too
        print(f"DEBUG: Fallback search by content matching")
        print(f"DEBUG: Searching for title='{self.title}', company='{self.company_name}', email='{self.contact_email}'")
        
        # Search for both live and draft pages
        potential_matches = ProjectPage.objects.filter(
            title=self.title,
            company_name=self.company_name,
            contact_email=self.contact_email
        )  # Removed .live() to include drafts
        
        print(f"DEBUG: Found {potential_matches.count()} potential matches (including drafts)")
        
        if potential_matches.exists():
            found_page = potential_matches.first()
            print(f"DEBUG: Using first match: {found_page} (ID: {found_page.id}, live: {found_page.live})")
            # Repair the broken link
            self.project_page = found_page
            self.save(update_fields=['project_page'])
            return found_page
        
        print(f"DEBUG: No project page found at all")
        return None
    
    @property
    def status_display(self):
        """Display status for admin list"""
        project_page = self.get_project_page()
        if project_page:
            return _("✅ Created")
        else:
            return _("⏳ Not created")
    
    @property 
    def project_link(self):
        """Get link to project page if it exists"""
        project_page = self.get_project_page()
        if project_page:
            from django.urls import reverse
            return reverse('wagtailadmin_pages:edit', args=[project_page.id])
        return None
    
    @property
    def locale_display(self):
        """Display locale for admin"""
        return dict(self._meta.get_field('locale').choices).get(self.locale, self.locale)
    
    @property
    def funding_display(self):
        """Display funding info for admin"""
        if self.is_funded and self.funding_amount:
            return f"✅ {self.funding_amount:,} ISK"
        elif self.is_funded:
            return "✅ Já (upphæð ekki tilgreind)"
        else:
            return "⏳ Ekki fjármagnað"
    
    def mark_as_viewed(self):
        """Mark this ad as viewed by admin"""
        if not self.viewed_at:
            from django.utils import timezone
            self.viewed_at = timezone.now()
            self.save(update_fields=['viewed_at'])


class ProjectIndexPage(Page):
    """Lists all live ProjectPage children."""
    # Optional introduction field for the top of the index page
    intro = RichTextField(blank=True)

    # Only ProjectPage children allowed under this page
    subpage_types = ["advertise.ProjectPage"]

    # This page can only live under the root (or change as you wish)
    parent_page_types = ["home.HomePage", "wagtailcore.Page"]  # adjust if needed

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    class Meta:
        verbose_name = _("Project index")

    # Provide children to the template context
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["projects"] = (
            self.get_children()
            .live()
            .specific()
            .order_by("-first_published_at")
        )
        return context


class ProjectApplication(models.Model):
    project_page = models.ForeignKey(
        'advertise.ProjectPage', 
        on_delete=models.CASCADE, 
        related_name='applications',
        verbose_name=_("Verkefni")
    )
    applicant = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'groups__name': 'Nemandi'},
        verbose_name=_("Umsækjandi")
    )
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Umsókn send"))
    status = models.CharField(
        _("Staða"),
        max_length=20,
        choices=[
            ('pending', _('Í bið')),
            ('accepted', _('Samþykkt')),
            ('rejected', _('Hafnað')),
        ],
        default='pending'
    )
    message = models.TextField(
        _("Skilaboð frá nemanda"), 
        blank=True, 
        help_text=_("Valfrjáls skilaboð frá umsækjanda")
    )
    
    class Meta:
        unique_together = ('project_page', 'applicant')  # Prevent duplicate applications
        verbose_name = _("Verkefnisumsókn")
        verbose_name_plural = _("Verkefnisumsóknir")
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.applicant.get_full_name() or self.applicant.username} → {self.project_page.title}"


class ProjectPage(Page):
    """
    A public-facing project entry that visitors will read.
    """
    description   = RichTextField(verbose_name=_("Lýsing"), blank=False)
    company_name  = models.CharField(_("Fyrirtæki"), max_length=200)
    contact_name  = models.CharField(_("Tengiliður"), max_length=120)
    contact_email = models.EmailField(_("Tengiliðapóstur"))
    other         = RichTextField(_("Annað"), blank=True)
    
    # NEW: Funding fields (copied from ProjectAd)
    is_funded      = models.BooleanField(_("Fjármagnað verkefni"), default=False)
    funding_amount = models.PositiveIntegerField(_("Fjárhæð (ISK)"), null=True, blank=True)
    
    # NEW: Requested advisors (copied from ProjectAd)
    requested_advisors = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Óskir um leiðbeinendur"),
        help_text=_("Starfsmenn sem fyrirtækið óskaði eftir sem leiðbeinendum"),
        limit_choices_to={'groups__name': 'Starfsmenn'},
        related_name='requested_project_pages'
    )

    # Field for the actual assigned instructors/supervisors
    leidbeinendur = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Leiðbeinendur"),
        help_text=_("Starfsmenn sem hafa tekið að sér þetta verkefni"),
        limit_choices_to={'groups__name': 'Starfsmenn'}
    )

    # NEW: Selected students field
    selected_students = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Valdir nemendur"),
        help_text=_("Nemendur sem hafa verið valdir fyrir þetta verkefni"),
        limit_choices_to={'groups__name': 'Nemandi'},
        related_name='assigned_projects'
    )

    # Only allowed beneath ProjectIndexPage
    parent_page_types = ["advertise.ProjectIndexPage"]
    subpage_types = []          # no children below a project page

    base_form_class = ProjectPageForm

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        MultiFieldPanel(
            [
                FieldPanel("company_name"),
                FieldPanel("contact_name"),
                FieldPanel("contact_email"),
            ],
            heading=_("Fyrirtæki og tengiliður"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("is_funded"),
                FieldPanel("funding_amount"),
            ],
            heading=_("Fjármögnun"),
        ),
        FieldPanel("other"),
        FieldPanel("requested_advisors"),
        FieldPanel("leidbeinendur"),
        FieldPanel("selected_students"),
    ]

    # Optional: makes fields searchable in Wagtail admin
    search_fields = Page.search_fields

    def get_context(self, request, *args, **kwargs):
        """Ensure request context is available in template and add people pages"""
        context = super().get_context(request, *args, **kwargs)
        
        # Check if user has already applied
        if request.user.is_authenticated:
            try:
                user_application = self.applications.get(applicant=request.user)
                context['user_application'] = user_application
            except ProjectApplication.DoesNotExist:
                context['user_application'] = None
        
        # Import here to avoid circular imports
        try:
            from people.models import PersonPage
            
            # Create a list of leidbeinendur with their corresponding person pages
            leidbeinendur_with_pages = []
            for leidbeinandi in self.leidbeinendur.all():
                try:
                    person_page = PersonPage.objects.live().filter(email=leidbeinandi.email).first()
                    leidbeinendur_with_pages.append({
                        'user': leidbeinandi,
                        'person_page': person_page
                    })
                except PersonPage.DoesNotExist:
                    leidbeinendur_with_pages.append({
                        'user': leidbeinandi,
                        'person_page': None
                    })
            
            context['leidbeinendur_with_pages'] = leidbeinendur_with_pages
            
            # Also create a list for requested advisors (for staff only)
            requested_advisors_with_pages = []
            for advisor in self.requested_advisors.all():
                try:
                    person_page = PersonPage.objects.live().filter(email=advisor.email).first()
                    requested_advisors_with_pages.append({
                        'user': advisor,
                        'person_page': person_page
                    })
                except PersonPage.DoesNotExist:
                    requested_advisors_with_pages.append({
                        'user': advisor,
                        'person_page': None
                    })
            
            context['requested_advisors_with_pages'] = requested_advisors_with_pages
            
            # Create a list for selected students with their corresponding person pages
            selected_students_with_pages = []
            for student in self.selected_students.all():
                try:
                    person_page = PersonPage.objects.live().filter(email=student.email).first()
                    selected_students_with_pages.append({
                        'user': student,
                        'person_page': person_page
                    })
                except PersonPage.DoesNotExist:
                    selected_students_with_pages.append({
                        'user': student,
                        'person_page': None
                    })
            
            context['selected_students_with_pages'] = selected_students_with_pages
            
        except ImportError:
            # If people app doesn't exist, just use the regular data
            context['leidbeinendur_with_pages'] = [
                {'user': user, 'person_page': None} 
                for user in self.leidbeinendur.all()
            ]
            context['requested_advisors_with_pages'] = [
                {'user': user, 'person_page': None} 
                for user in self.requested_advisors.all()
            ]
            context['selected_students_with_pages'] = [
                {'user': user, 'person_page': None} 
                for user in self.selected_students.all()
            ]
        
        return context

    class Meta:
        verbose_name = _("Verkefni")