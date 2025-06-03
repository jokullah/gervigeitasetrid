from django import forms
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
            "other",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "other":       forms.Textarea(attrs={"rows": 4}),
        }
