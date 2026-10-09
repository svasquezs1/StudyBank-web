from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from tutoring.models import TutoringRequest

from .models import Notification


def display_name(user):
    """Full name when the user has filled it in (RF-03), email otherwise."""
    return user.get_full_name() or user.email


@receiver(post_save, sender=TutoringRequest)
def notify_tutor_of_new_request(sender, instance, created, **kwargs):
    """RF-19: notify the tutor as soon as a student submits a request."""
    if not created:
        return

    Notification.objects.create(
        recipient=instance.tutor.user,
        tutoring_request=instance,
        message=(
            f"Student {display_name(instance.student)} has requested "
            f"a tutoring session for {instance.subject.name}."
        ),
        link=(
            f"{reverse('tutoring:incoming_requests')}"
            f"#request-{instance.pk}"
        ),
    )
