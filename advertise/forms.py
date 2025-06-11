from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import ProjectAd, ProjectApplication
from datetime import date


class ProjectAdForm(forms.ModelForm):
    class Meta:
        model  = ProjectAd
        fields = [
            "title",
            "description",
            "company_name",
            "contact_name",
            "contact_email",
            "time_limit",  # ADD THIS LINE
            "is_funded",
            "funding_amount",
            "requested_advisors",
            "other",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "other": forms.Textarea(attrs={"rows": 4}),
            "funding_amount": forms.NumberInput(attrs={
                "placeholder": _("t.d. 500000"),
                "step": "1000",
                "min": "0"
            }),
            # ADD THIS: Custom widget for time_limit field
            "time_limit": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
                "placeholder": _("YYYY-MM-DD")
            }),
            # Changed to CheckboxSelectMultiple for better UX
            "requested_advisors": forms.CheckboxSelectMultiple(attrs={
                "class": "advisor-checkbox-list",
            }),
        }
        labels = {
            "is_funded": _("Er verkefnið fjármagnað?"),
            "funding_amount": _("Fjárhæð (ISK)"),
            "requested_advisors": _("Óskir um leiðbeinendur"),
            "time_limit": _("Umsóknarfrestur verkefnis (valfrjálst)"),  # ADD THIS LINE
        }
        help_texts = {
            "is_funded": _("Krossa við ef verkefnið er fjármagnað"),
            "funding_amount": _("Heildarfjárhæð verkefnisins í íslenskum krónum (valfrjálst)"),
            "requested_advisors": _("Veljið þá starfsmenn sem þið viljið helst fá sem leiðbeinendur. Smellið á hvern starfsmann til að velja/afvelja."),
            "time_limit": _("Umsóknarfrestur fyrir nemendur og starfsmenn. Verkefnið verður ekki sýnilegt að honum liðnum. Ef þessum reit er skilað tómum verður verkefnið til sýnis þar til admin tekur það niður eða haft er samband."),  # ADD THIS LINE
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff members in the advisor selection
        self.fields['requested_advisors'].queryset = User.objects.filter(
            groups__name='Starfsmenn'
        ).order_by('first_name', 'last_name')
        
        # Customize the display of advisor choices
        self.fields['requested_advisors'].label_from_instance = lambda obj: (
            f"{obj.get_full_name()}" if obj.get_full_name() else f"{obj.username}"
        )
        
        # Make funding amount field dependent on is_funded
        self.fields['funding_amount'].required = False
        
        # Make time_limit field optional and set min date to today
        self.fields['time_limit'].required = False
        
    def clean_time_limit(self):
        """Validate that time_limit is not in the past"""
        time_limit = self.cleaned_data.get('time_limit')
        
        if time_limit and time_limit < date.today():
            raise forms.ValidationError(
                _("Tímamörk geta ekki verið í fortíðinni. Veljið dagsetningu í framtíðinni.")
            )
        
        return time_limit
        
    def clean(self):
        cleaned_data = super().clean()
        is_funded = cleaned_data.get('is_funded')
        funding_amount = cleaned_data.get('funding_amount')
        
        # If project is marked as funded but no amount given, that's OK
        # If project is not funded, clear the funding amount
        if not is_funded:
            cleaned_data['funding_amount'] = None
            
        return cleaned_data


class ProjectApplicationForm(forms.ModelForm):
    """Form for students to apply to projects"""
    
    class Meta:
        model = ProjectApplication
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': _('Skrifaðu stuttan texta um hvers vegna þú vilt taka þátt í þessu verkefni (valfrjálst)'),
                'class': 'form-control'
            })
        }
        labels = {
            'message': _('Skilaboð til fyrirtækisins')
        }
        help_texts = {
            'message': _('Þessi texti verður sendur til fyrirtækisins ásamt umsókninni þinni')
        }