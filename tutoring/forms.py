from django import forms
from django.utils import timezone

from .models import Subject, TutoringRequest, TutorProfile


class TutorRegistrationForm(forms.ModelForm):
    class Meta:
        model = TutorProfile
        fields = ("subjects",)
        widgets = {
            "subjects": forms.CheckboxSelectMultiple(),
        }


class TutoringRequestForm(forms.ModelForm):
    class Meta:
        model = TutoringRequest
        fields = (
            "subject",
            "scheduled_at",
            "mode",
            "message",
        )
        labels = {
            "subject": "Subject",
            "scheduled_at": "Preferred date and time",
            "mode": "Tutoring mode",
            "message": "Message for the tutor",
        }
        widgets = {
            "scheduled_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
            "message": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Tell the tutor what you need help with...",
                }
            ),
        }

    def __init__(self, *args, tutor=None, **kwargs):
        super().__init__(*args, **kwargs)

        if tutor is not None:
            self.fields["subject"].queryset = tutor.subjects.all().order_by(
                "name"
            )
        else:
            self.fields["subject"].queryset = Subject.objects.none()

    def clean_scheduled_at(self):
        scheduled_at = self.cleaned_data["scheduled_at"]

        if scheduled_at <= timezone.now():
            raise forms.ValidationError(
                "The tutoring session must be scheduled for a future date and time."
            )

        return scheduled_at
