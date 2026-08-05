from django import forms

from .models import Material


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('title', 'description', 'course', 'university', 'file_type', 'file')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Midterm Exam Summary'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional brief description of the material...'}),
            'course': forms.Select(),
            'university': forms.Select(),
            'file_type': forms.Select(),
        }
