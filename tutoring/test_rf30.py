from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Subject,
    TutoringRequest,
    TutorProfile,
)


User = get_user_model()


class RF30TutorStatisticsTests(TestCase):
    def setUp(self):
        self.password = "TestPassword123!"

        self.tutor_user = User.objects.create_user(
            email="tutor@eafit.edu.co",
            password=self.password,
        )

        self.other_tutor_user = User.objects.create_user(
            email="othertutor@eafit.edu.co",
            password=self.password,
        )

        self.student = User.objects.create_user(
            email="student@eafit.edu.co",
            password=self.password,
        )

        self.non_tutor = User.objects.create_user(
            email="nontutor@eafit.edu.co",
            password=self.password,
        )

        self.tutor = TutorProfile.objects.create(
            user=self.tutor_user,
            is_approved=True,
        )

        self.other_tutor = TutorProfile.objects.create(
            user=self.other_tutor_user,
            is_approved=True,
        )

        self.subject = Subject.objects.create(
            name="Calculus"
        )

    def create_request(
        self,
        tutor=None,
        status=TutoringRequest.Status.PENDING,
    ):
        return TutoringRequest.objects.create(
            student=self.student,
            tutor=tutor or self.tutor,
            subject=self.subject,
            scheduled_at=(
                timezone.now()
                + timedelta(days=2)
            ),
            mode=TutoringRequest.Mode.VIRTUAL,
            status=status,
        )

    def login_tutor(self):
        self.client.login(
            email=self.tutor_user.email,
            password=self.password,
        )

    def test_statistics_requires_authentication(self):
        response = self.client.get(
            reverse("tutoring:statistics")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_non_tutor_cannot_access_statistics(self):
        self.client.login(
            email=self.non_tutor.email,
            password=self.password,
        )

        response = self.client.get(
            reverse("tutoring:statistics")
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_registered_tutor_can_access_statistics(self):
        self.login_tutor()

        response = self.client.get(
            reverse("tutoring:statistics")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTemplateUsed(
            response,
            "tutoring/statistics.html",
        )

    def test_dashboard_displays_required_metrics(self):
        self.create_request(
            status=TutoringRequest.Status.PENDING
        )

        self.create_request(
            status=TutoringRequest.Status.ACCEPTED
        )

        self.create_request(
            status=TutoringRequest.Status.ACCEPTED
        )

        self.create_request(
            status=TutoringRequest.Status.REJECTED
        )

        self.create_request(
            status=TutoringRequest.Status.CANCELED
        )

        self.login_tutor()

        response = self.client.get(
            reverse("tutoring:statistics")
        )

        statistics = response.context["statistics"]

        self.assertEqual(
            statistics["total_requests"],
            5,
        )

        self.assertEqual(
            statistics["accepted_sessions"],
            2,
        )

        self.assertEqual(
            statistics["rejected_sessions"],
            1,
        )

        self.assertEqual(
            statistics["canceled_sessions"],
            1,
        )

    def test_statistics_only_include_current_tutor(self):
        self.create_request(
            status=TutoringRequest.Status.ACCEPTED
        )

        self.create_request(
            tutor=self.other_tutor,
            status=TutoringRequest.Status.REJECTED,
        )

        self.login_tutor()

        response = self.client.get(
            reverse("tutoring:statistics")
        )

        statistics = response.context["statistics"]

        self.assertEqual(
            statistics["total_requests"],
            1,
        )

        self.assertEqual(
            statistics["accepted_sessions"],
            1,
        )

        self.assertEqual(
            statistics["rejected_sessions"],
            0,
        )

    def test_metrics_update_from_database(self):
        self.login_tutor()

        first_response = self.client.get(
            reverse("tutoring:statistics")
        )

        self.assertEqual(
            first_response.context[
                "statistics"
            ]["total_requests"],
            0,
        )

        self.create_request(
            status=TutoringRequest.Status.CANCELED
        )

        second_response = self.client.get(
            reverse("tutoring:statistics")
        )

        self.assertEqual(
            second_response.context[
                "statistics"
            ]["total_requests"],
            1,
        )

        self.assertEqual(
            second_response.context[
                "statistics"
            ]["canceled_sessions"],
            1,
        )

    def test_dashboard_uses_summary_cards(self):
        self.login_tutor()

        response = self.client.get(
            reverse("tutoring:statistics")
        )

        self.assertContains(
            response,
            "TOTAL REQUESTS RECEIVED",
        )

        self.assertContains(
            response,
            "TOTAL ACCEPTED SESSIONS",
        )

        self.assertContains(
            response,
            "TOTAL REJECTED SESSIONS",
        )

        self.assertContains(
            response,
            "TOTAL CANCELED SESSIONS",
        )

        self.assertContains(
            response,
            'class="tutor-card"',
            count=4,
        )

    def test_statistics_link_appears_for_tutor(self):
        self.login_tutor()

        response = self.client.get(
            reverse("tutoring:statistics")
        )

        self.assertContains(
            response,
            reverse("tutoring:statistics"),
        )

        self.assertContains(
            response,
            "Statistics",
        )
