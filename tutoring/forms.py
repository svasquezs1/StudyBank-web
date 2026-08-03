from django import forms

from .models import TutorProfile


class TutorRegistrationForm(forms.ModelForm):
    class Meta:
        model = TutorProfile
        fields = ("subjects",)
        widgets = {
            "subjects": forms.CheckboxSelectMultiple(),
        }