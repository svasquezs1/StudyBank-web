from django import forms

from accounts.models import University

from .models import Course, Material


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('title', 'course', 'university', 'file_type', 'file')
        widgets = {
            'course': forms.Select(),
            'university': forms.Select(),
            'file_type': forms.Select(),
        }
