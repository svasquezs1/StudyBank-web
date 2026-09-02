from django import forms
from .models import Material


class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ('title', 'description', 'course', 'university', 'file_type', 'file')
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g., Midterm Exam Summary'}),
            'description': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Optional brief description of the material...',
                'style': 'width: 100%; background: var(--ink); color: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: .65rem .75rem; font-family: inherit; font-size: .9rem;'
            }),
            'course': forms.Select(),
            'university': forms.Select(),
            'file_type': forms.Select(),
        }

class MaterialSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        strip=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por título, materia o descripción...',
            'class': 'form-control',
            'type': 'search',
        })
    )
