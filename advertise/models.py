from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from django.utils.translation import gettext_lazy as _
from wagtail.search.index import SearchField
from django.contrib.auth.models import User


class ProjectAd(models.Model):
    title          = models.CharField("Titill",   max_length=200)
    description    = models.TextField("Lýsing")
    company_name   = models.CharField("Fyrirtæki", max_length=200)
    contact_name   = models.CharField("Tengiliður", max_length=120)
    contact_email  = models.EmailField("Tengiliðapóstur")
    other          = models.TextField("Annað", blank=True)
    submitted_at   = models.DateTimeField(auto_now_add=True)
    
    # New field to track the associated project page
    project_page   = models.ForeignKey(
        'advertise.ProjectPage', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Tengd verkefnasíða",
        help_text="Verkefnasíða sem búin var til úr þessari auglýsingu"
    )

    class Meta:
        verbose_name        = "Auglýst verkefni"
        verbose_name_plural = "Auglýst verkefni"
        ordering            = ["-submitted_at"]

    def __str__(self):
        return f"{self.title} ({self.company_name})"
    
    @property
    def has_project_page(self):
        """Check if this ad has been converted to a project page"""
        return self.project_page is not None

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


    # New field for the instructor/supervisor
    # New field for the instructors/supervisors - many-to-many relationship
    leidbeinendur = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Leiðbeinendur"),
        help_text=_("Starfsmenn sem hafa tekið að sér þetta verkefni"),
        limit_choices_to={'groups__name': 'Starfsmenn'}
    )

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
        FieldPanel("leidbeinendur"),
    ]

    # Optional: makes fields searchable in Wagtail admin
    search_fields = Page.search_fields

    class Meta:
        verbose_name = _("Project")
