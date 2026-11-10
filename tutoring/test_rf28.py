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


class RF28TutoringCancellationTests(TestCase):
    def setUp(self):
        self.password = "TestPassword123!"

        self.student = User.objects.create_user(
            email="student@eafit.edu.co",
            password=self.password,
        )

        self.other_student = User.objects.create_user(
            email="other@eafit.edu.co",
            password=self.password,
        )

        self.tutor_user = User.objects.create_user(
            email="tutor@eafit.edu.co",
            password=self.password,
        )

        self.subject = Subject.objects.create(
            name="Calculus"
        )

        self.tutor = TutorProfile.objects.create(
            user=self.tutor_user,
            is_approved=True,
        )

        self.tutor.subjects.add(
            self.subject
        )

    def create_request(
        self,
        status=TutoringRequest.Status.PENDING,
    ):
        return TutoringRequest.objects.create(
            student=self.student,
            tutor=self.tutor,
            subject=self.subject,
            scheduled_at=(
                timezone.now()
                + timedelta(days=2)
            ),
            mode=TutoringRequest.Mode.VIRTUAL,
            status=status,
        )

    def login_student(self):
        self.client.login(
            email=self.student.email,
            password=self.password,
        )

    def test_cancel_requires_authentication(self):
        tutoring_request = self.create_request()

        response = self.client.post(
            reverse(
                "tutoring:cancel_request",
                args=[tutoring_request.id],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertIn(
            reverse("accounts:login"),
            response.url,
        )

    def test_pending_request_can_be_canceled(self):
        tutoring_request = self.create_request()

        self.login_student()

        response = self.client.post(
            reverse(
                "tutoring:cancel_request",
                args=[tutoring_request.id],
            )
        )

        tutoring_request.refresh_from_db()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.CANCELED,
        )

        self.assertRedirects(
            response,
            reverse("tutoring:my_requests")
            + "?canceled=1",
        )

    def test_accepted_request_can_be_canceled(self):
        tutoring_request = self.create_request(
            TutoringRequest.Status.ACCEPTED
        )

        self.login_student()

        self.client.post(
            reverse(
                "tutoring:cancel_request",
                args=[tutoring_request.id],
            )
        )

        tutoring_request.refresh_from_db()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.CANCELED,
        )

    def test_locked_requests_cannot_be_canceled(self):
        self.login_student()

        locked_statuses = (
            TutoringRequest.Status.REJECTED,
            TutoringRequest.Status.COMPLETED,
            TutoringRequest.Status.CANCELED,
        )

        for status in locked_statuses:
            with self.subTest(status=status):
                tutoring_request = self.create_request(
                    status
                )

                self.client.post(
                    reverse(
                        "tutoring:cancel_request",
                        args=[tutoring_request.id],
                    )
                )

                tutoring_request.refresh_from_db()

                self.assertEqual(
                    tutoring_request.status,
                    status,
                )

    def test_student_cannot_cancel_another_students_request(
        self
    ):
        tutoring_request = self.create_request()

        self.client.login(
            email=self.other_student.email,
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tutoring:cancel_request",
                args=[tutoring_request.id],
            )
        )

        self.assertEqual(response.status_code, 404)

        tutoring_request.refresh_from_db()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.PENDING,
        )

    def test_cancel_endpoint_only_accepts_post(self):
        tutoring_request = self.create_request()

        self.login_student()

        response = self.client.get(
            reverse(
                "tutoring:cancel_request",
                args=[tutoring_request.id],
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_pending_request_shows_cancel_action(self):
        tutoring_request = self.create_request()

        self.login_student()

        response = self.client.get(
            reverse("tutoring:my_requests")
        )

        self.assertContains(
            response,
            reverse(
                "tutoring:cancel_request",
                args=[tutoring_request.id],
            ),
        )

        self.assertContains(
            response,
            "Cancel Request",
        )

    def test_canceled_request_shows_locked_action(self):
        self.create_request(
            TutoringRequest.Status.CANCELED
        )

        self.login_student()

        response = self.client.get(
            reverse("tutoring:my_requests")
        )

        self.assertContains(
            response,
            "Cancel Request",
        )

        self.assertContains(
            response,
            "disabled",
        )

    def test_tutor_dashboard_reflects_canceled_status(
        self
    ):
        tutoring_request = self.create_request()

        self.login_student()

        self.client.post(
            reverse(
                "tutoring:cancel_request",
                args=[tutoring_request.id],
            )
        )

        self.client.logout()

        self.client.login(
            email=self.tutor_user.email,
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tutoring:incoming_requests"
            )
        )

        self.assertContains(
            response,
            "Canceled",
        )

        self.assertContains(
            response,
            "This request has already been",
        )

        self.assertContains(
            response,
            "canceled.",
        )
