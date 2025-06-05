from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import ProjectAd

class ProjectAdForm(forms.ModelForm):
    class Meta:
        model  = ProjectAd
        fields = [
            "title",
            "description",
            "company_name",
            "contact_name",
            "contact_email",
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
            "requested_advisors": forms.SelectMultiple(attrs={
                "class": "advisor-select",
                "size": "8",
                "style": "width: 100%; min-height: 200px;"
            }),
        }
        labels = {
            "is_funded": _("Er verkefnið fjármagnað?"),
            "funding_amount": _("Fjárhæð (ISK)"),
            "requested_advisors": _("Óskir um leiðbeinendur"),
        }
        help_texts = {
            "is_funded": _("Krossa við ef verkefnið er fjármagnað"),
            "funding_amount": _("Heildarfjárhæð verkefnisins í íslenskum krónum (valfrjálst)"),
            "requested_advisors": _("Veljið þá starfsmenn sem þið viljið helst fá sem leiðbeinendur. Haldið niðri Ctrl/Cmd og smellið til að velja marga."),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show staff members in the advisor selection
        self.fields['requested_advisors'].queryset = User.objects.filter(
            groups__name='Starfsmenn'
        ).order_by('first_name', 'last_name')
        
        # Customize the display of advisor choices
        self.fields['requested_advisors'].label_from_instance = lambda obj: (
            f"{obj.get_full_name()} ({obj.email})" if obj.get_full_name() else f"{obj.username} ({obj.email})"
        )
        
        # Make funding amount field dependent on is_funded
        self.fields['funding_amount'].required = False
        
    def clean(self):
        cleaned_data = super().clean()
        is_funded = cleaned_data.get('is_funded')
        funding_amount = cleaned_data.get('funding_amount')
        
        # If project is marked as funded but no amount given, that's OK
        # If project is not funded, clear the funding amount
        if not is_funded:
            cleaned_data['funding_amount'] = None
            
        return cleaned_data
