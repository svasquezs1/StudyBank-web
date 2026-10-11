from django.db.models.signals import post_save, pre_save
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


@receiver(pre_save, sender=TutoringRequest)
def remember_previous_status(sender, instance, **kwargs):
    """Stores the status the request had before this save (RF-20)."""
    if instance.pk is None:
        instance._previous_status = None
        return

    instance._previous_status = (
        TutoringRequest.objects.filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
    )


@receiver(post_save, sender=TutoringRequest)
def notify_student_of_decision(sender, instance, created, **kwargs):
    """RF-20: notify the student as soon as the tutor accepts or rejects."""
    if created:
        return

    decided = (
        TutoringRequest.Status.ACCEPTED,
        TutoringRequest.Status.REJECTED,
    )
    previous_status = getattr(instance, "_previous_status", None)

    if instance.status not in decided or previous_status == instance.status:
        return

    Notification.objects.create(
        recipient=instance.student,
        tutoring_request=instance,
        message=(
            f"Tutor {display_name(instance.tutor.user)} has "
            f"{instance.get_status_display().lower()} your tutoring "
            f"request for {instance.subject.name}."
        ),
        link=f"{reverse('tutoring:my_requests')}#request-{instance.pk}",
    )
