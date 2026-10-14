from django import forms
from django.utils import timezone

from .models import (
    Subject,
    TutorAvailability,
    TutoringRequest,
    TutorProfile,
)


class TutorRegistrationForm(forms.ModelForm):
    class Meta:
        model = TutorProfile
        fields = ("subjects",)
        widgets = {
            "subjects": forms.CheckboxSelectMultiple(),
        }


class TutorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = TutorAvailability
        fields = (
            "day_of_week",
            "start_time",
            "end_time",
        )
        labels = {
            "day_of_week": "Day",
            "start_time": "Start time",
            "end_time": "End time",
        }
        widgets = {
            "start_time": forms.TimeInput(
                attrs={"type": "time"}
            ),
            "end_time": forms.TimeInput(
                attrs={"type": "time"}
            ),
        }

    def __init__(self, *args, tutor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tutor = tutor

    def clean(self):
        cleaned_data = super().clean()

        day_of_week = cleaned_data.get("day_of_week")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if not all(
            value is not None
            for value in (
                day_of_week,
                start_time,
                end_time,
            )
        ):
            return cleaned_data

        if end_time <= start_time:
            raise forms.ValidationError(
                "End time must be later than start time."
            )

        if self.tutor is not None:
            overlapping_slots = TutorAvailability.objects.filter(
                tutor=self.tutor,
                day_of_week=day_of_week,
                is_active=True,
                start_time__lt=end_time,
                end_time__gt=start_time,
            )

            if self.instance.pk:
                overlapping_slots = overlapping_slots.exclude(
                    pk=self.instance.pk
                )

            if overlapping_slots.exists():
                raise forms.ValidationError(
                    "This availability overlaps with an existing time slot."
                )

        return cleaned_data


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
        self.tutor = tutor

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

        if self.tutor is not None:
            local_scheduled_at = timezone.localtime(scheduled_at)

            weekday = local_scheduled_at.weekday()
            scheduled_time = local_scheduled_at.time()

            available = TutorAvailability.objects.filter(
                tutor=self.tutor,
                day_of_week=weekday,
                is_active=True,
                start_time__lte=scheduled_time,
                end_time__gt=scheduled_time,
            ).exists()

            if not available:
                raise forms.ValidationError(
                    "The selected date and time is outside the tutor's available schedule."
                )

        return scheduled_at
    