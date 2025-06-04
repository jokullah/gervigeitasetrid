from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from django.utils.translation import gettext_lazy as _
from wagtail.search.index import SearchField


class ProjectAd(models.Model):
    title          = models.CharField(_("Titill"), max_length=200) 
    description    = models.TextField(_("Lýsing")) 
    company_name   = models.CharField(_("Fyrirtæki"), max_length=200) 
    contact_name   = models.CharField(_("Tengiliður"), max_length=120) 
    contact_email  = models.EmailField(_("Tengiliðapóstur")) 
    other          = models.TextField(_("Annað"), blank=True) 
    submitted_at   = models.DateTimeField(auto_now_add=True)
    
    # NEW: Track if admin has viewed this ad
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
        """Check if this ad has been converted to a project page"""
        return self.project_page is not None
    
    @property
    def status_display(self):
        """Display status for admin list"""
        if self.project_page:
            return _("✅ Created")
        else:
            return _("⏳ Not created")
    
    @property 
    def project_link(self):
        """Get link to project page if it exists"""
        if self.project_page:
            from django.urls import reverse
            return reverse('wagtailadmin_pages:edit', args=[self.project_page.id])
        return None
    
    @property
    def locale_display(self):
        """Display locale for admin"""
        return dict(self._meta.get_field('locale').choices).get(self.locale, self.locale)
    
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

class ProjectPage(Page):
    """
    A public-facing project entry that visitors will read.
    """
    description   = RichTextField(verbose_name=_("Lýsing"), blank=False)
    company_name  = models.CharField(_("Fyrirtæki"), max_length=200)
    contact_name  = models.CharField(_("Tengiliður"), max_length=120)
    contact_email = models.EmailField(_("Tengiliðapóstur"))
    other         = RichTextField(_("Annað"), blank=True)

    # Only allowed beneath ProjectIndexPage
    parent_page_types = ["advertise.ProjectIndexPage"]
    subpage_types = []          # no children below a project page

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        MultiFieldPanel(
            [
                FieldPanel("company_name"),
                FieldPanel("contact_name"),
                FieldPanel("contact_email"),
            ],
            heading=_("Company & contact"),
        ),
        FieldPanel("other"),
    ]

    # Optional: makes fields searchable in Wagtail admin
    search_fields = Page.search_fields

    class Meta:
        verbose_name = _("Project")
