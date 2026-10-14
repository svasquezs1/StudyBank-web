from django.conf import settings
from django.db import models


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class TutorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutor_profile",
    )
    subjects = models.ManyToManyField(
        Subject,
        related_name="tutors",
    )
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Tutor: {self.user.email}"


class TutorAvailability(models.Model):
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    tutor = models.ForeignKey(
        TutorProfile,
        on_delete=models.CASCADE,
        related_name="availability_slots",
    )
    day_of_week = models.PositiveSmallIntegerField(
        choices=DayOfWeek.choices,
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = [
            "day_of_week",
            "start_time",
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "tutor",
                    "day_of_week",
                    "start_time",
                    "end_time",
                ],
                name="unique_tutor_availability_slot",
            )
        ]

    def __str__(self):
        return (
            f"{self.tutor.user.email} - "
            f"{self.get_day_of_week_display()} "
            f"{self.start_time} to {self.end_time}"
        )


class TutoringRequest(models.Model):
    class Mode(models.TextChoices):
        IN_PERSON = "in_person", "In person"
        VIRTUAL = "virtual", "Virtual"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutoring_requests_sent",
    )
    tutor = models.ForeignKey(
        TutorProfile,
        on_delete=models.CASCADE,
        related_name="tutoring_requests_received",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="tutoring_requests",
    )
    scheduled_at = models.DateTimeField()
    mode = models.CharField(
        max_length=20,
        choices=Mode.choices,
    )
    message = models.TextField(
        max_length=500,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.student.email} -> {self.tutor.user.email} "
            f"({self.subject.name})"
        )
    