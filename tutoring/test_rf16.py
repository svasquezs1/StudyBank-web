from datetime import time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Program, University

from .models import (
    Subject,
    TutorAvailability,
    TutoringRating,
    TutoringRequest,
    TutorProfile,
)


User = get_user_model()


class TutorProfileTests(TestCase):
    """RF-16: tutor public profile with average rating."""

    def setUp(self):
        self.password = "TestPassword123!"

        university = University.objects.create(name="Universidad EAFIT")
        program = Program.objects.create(
            name="Systems Engineering",
            university=university,
        )

        self.viewer = User.objects.create_user(
            email="viewer@eafit.edu.co",
            password=self.password,
        )
        self.tutor_user = User.objects.create_user(
            email="tutor@eafit.edu.co",
            password=self.password,
            first_name="Carlos",
            last_name="Gomez",
            university=university,
            program=program,
        )

        self.subject = Subject.objects.create(name="Calculus")
        self.tutor = TutorProfile.objects.create(
            user=self.tutor_user,
            is_approved=True,
        )
        self.tutor.subjects.add(self.subject)

        self.url = reverse("tutoring:tutor_profile", args=[self.tutor.id])

    def login(self, user=None):
        self.client.login(
            email=(user or self.viewer).email,
            password=self.password,
        )

    def add_rating(self, score, feedback=""):
        student = User.objects.create_user(
            email=f"student{TutoringRating.objects.count()}@eafit.edu.co",
            password=self.password,
        )
        tutoring_request = TutoringRequest.objects.create(
            student=student,
            tutor=self.tutor,
            subject=self.subject,
            scheduled_at=timezone.now() - timedelta(days=1),
            mode=TutoringRequest.Mode.VIRTUAL,
            status=TutoringRequest.Status.COMPLETED,
        )
        return TutoringRating.objects.create(
            tutoring_request=tutoring_request,
            student=student,
            tutor=self.tutor,
            score=score,
            feedback=feedback,
        )

    def test_profile_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_nonexistent_tutor_returns_404(self):
        self.login()

        response = self.client.get(
            reverse("tutoring:tutor_profile", args=[9999])
        )

        self.assertEqual(response.status_code, 404)

    def test_unapproved_tutor_returns_404(self):
        self.tutor.is_approved = False
        self.tutor.save()
        self.login()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_profile_shows_personal_details_and_subjects(self):
        self.login()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, "Carlos Gomez")
        self.assertContains(response, "Universidad EAFIT")
        self.assertContains(response, "Systems Engineering")
        self.assertContains(response, "Calculus")
        self.assertContains(response, "In person")
        self.assertContains(response, "Virtual")

    def test_profile_shows_active_availability_only(self):
        TutorAvailability.objects.create(
            tutor=self.tutor,
            day_of_week=TutorAvailability.DayOfWeek.TUESDAY,
            start_time=time(14, 0),
            end_time=time(16, 0),
        )
        TutorAvailability.objects.create(
            tutor=self.tutor,
            day_of_week=TutorAvailability.DayOfWeek.FRIDAY,
            start_time=time(8, 0),
            end_time=time(9, 0),
            is_active=False,
        )
        self.login()

        response = self.client.get(self.url)

        self.assertContains(response, "Tuesday")
        self.assertContains(response, "14:00")
        self.assertNotContains(response, "Friday")

    def test_profile_without_ratings_shows_informative_state(self):
        self.login()

        response = self.client.get(self.url)

        self.assertContains(response, "No ratings yet")

    def test_profile_shows_average_and_total_ratings(self):
        self.add_rating(5)
        self.add_rating(4)
        self.add_rating(4)
        self.login()

        response = self.client.get(self.url)

        self.assertEqual(response.context["ratings_total"], 3)
        self.assertAlmostEqual(response.context["average_rating"], 4.333, places=2)
        self.assertContains(response, "4.3 / 5")
        self.assertContains(response, "3 ratings")
        self.assertNotContains(response, "No ratings yet")

    def test_profile_shows_recent_review_feedback(self):
        self.add_rating(5, feedback="Explained limits very clearly")
        self.login()

        response = self.client.get(self.url)

        self.assertContains(response, "Explained limits very clearly")

    def test_other_users_see_request_button(self):
        self.login()

        response = self.client.get(self.url)

        self.assertContains(
            response,
            reverse("tutoring:request_tutoring", args=[self.tutor.id]),
        )

    def test_tutor_does_not_see_request_button_on_own_profile(self):
        self.login(self.tutor_user)

        response = self.client.get(self.url)

        self.assertNotContains(
            response,
            reverse("tutoring:request_tutoring", args=[self.tutor.id]),
        )

    def test_tutor_search_links_to_profile(self):
        self.login()

        response = self.client.get(reverse("tutoring:tutor_search"))

        self.assertContains(response, self.url)
        self.assertContains(response, "Carlos Gomez")
