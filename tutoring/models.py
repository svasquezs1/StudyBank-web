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