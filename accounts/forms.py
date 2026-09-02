from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Program, University, User


class RegisterForm(UserCreationForm):
    university = forms.ModelChoiceField(
        queryset=University.objects.all(),
        required=True,
        empty_label='Select your university',
    )
    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        required=True,
        empty_label='Select your program',
    )

    class Meta:
        model = User
        fields = ('email', 'university', 'program', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'placeholder': 'you@eafit.edu.co'})
        self.fields['password1'].widget.attrs.update({'placeholder': '••••••••'})
        self.fields['password2'].widget.attrs.update({'placeholder': '••••••••'})


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'university', 'program', 'profile_picture')
        widgets = {
            'profile_picture': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['university'].empty_label = 'Select your university'
        self.fields['program'].empty_label = 'Select your program'
        self.fields['profile_picture'].required = False

