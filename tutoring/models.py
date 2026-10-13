from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Subject(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
    )

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

    is_approved = models.BooleanField(
        default=False,
    )

    @property
    def average_rating(self):
        ratings = self.ratings.all()

        if not ratings.exists():
            return None

        return ratings.aggregate(
            average=models.Avg("score")
        )["average"]

    @property
    def ratings_count(self):
        return self.ratings.count()

    def __str__(self):
        return f"Tutor: {self.user.email}"


class TutoringRequest(models.Model):
    class Mode(models.TextChoices):
        IN_PERSON = (
            "in_person",
            "In person",
        )

        VIRTUAL = (
            "virtual",
            "Virtual",
        )

    class Status(models.TextChoices):
        PENDING = (
            "pending",
            "Pending",
        )

        ACCEPTED = (
            "accepted",
            "Accepted",
        )

        REJECTED = (
            "rejected",
            "Rejected",
        )

        COMPLETED = (
            "completed",
            "Completed",
        )

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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.student.email} -> "
            f"{self.tutor.user.email} "
            f"({self.subject.name})"
        )


class TutoringRating(models.Model):
    tutoring_request = models.OneToOneField(
        TutoringRequest,
        on_delete=models.CASCADE,
        related_name="rating",
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutoring_ratings_given",
    )

    tutor = models.ForeignKey(
        TutorProfile,
        on_delete=models.CASCADE,
        related_name="ratings",
    )

    score = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )

    feedback = models.TextField(
        max_length=1000,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

    def __str__(self):
        return (
            f"{self.student.email} rated "
            f"{self.tutor.user.email}: "
            f"{self.score}/5"
        )
