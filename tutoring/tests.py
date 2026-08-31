from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Subject, TutoringRequest, TutorProfile


User = get_user_model()


class TutoringRequestTests(TestCase):
    def setUp(self):
        self.password = "TestPassword123!"

        self.student = User.objects.create_user(
            email="student@eafit.edu.co",
            password=self.password,
        )

        self.tutor_user = User.objects.create_user(
            email="tutor@eafit.edu.co",
            password=self.password,
        )

        self.subject = Subject.objects.create(
            name="Calculus",
        )

        self.tutor = TutorProfile.objects.create(
            user=self.tutor_user,
            is_approved=True,
        )

        self.tutor.subjects.add(self.subject)

    def test_authenticated_student_can_request_tutoring(self):
        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        scheduled_at = timezone.now() + timedelta(days=2)

        response = self.client.post(
            reverse(
                "tutoring:request_tutoring",
                args=[self.tutor.id],
            ),
            {
                "subject": self.subject.id,
                "scheduled_at": scheduled_at.strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "mode": TutoringRequest.Mode.VIRTUAL,
                "message": "I need help with Calculus.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(TutoringRequest.objects.count(), 1)

        tutoring_request = TutoringRequest.objects.first()

        self.assertEqual(
            tutoring_request.student,
            self.student,
        )
        self.assertEqual(
            tutoring_request.tutor,
            self.tutor,
        )
        self.assertEqual(
            tutoring_request.subject,
            self.subject,
        )
        self.assertEqual(
            tutoring_request.mode,
            TutoringRequest.Mode.VIRTUAL,
        )
        self.assertEqual(
            tutoring_request.message,
            "I need help with Calculus.",
        )

    def test_new_request_has_pending_status(self):
        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        scheduled_at = timezone.now() + timedelta(days=2)

        self.client.post(
            reverse(
                "tutoring:request_tutoring",
                args=[self.tutor.id],
            ),
            {
                "subject": self.subject.id,
                "scheduled_at": scheduled_at.strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "mode": TutoringRequest.Mode.IN_PERSON,
                "message": "I need help preparing for an exam.",
            },
        )

        tutoring_request = TutoringRequest.objects.first()

        self.assertIsNotNone(tutoring_request)
        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.PENDING,
        )

    def test_past_date_is_rejected(self):
        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        past_date = timezone.now() - timedelta(days=1)

        response = self.client.post(
            reverse(
                "tutoring:request_tutoring",
                args=[self.tutor.id],
            ),
            {
                "subject": self.subject.id,
                "scheduled_at": past_date.strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "mode": TutoringRequest.Mode.VIRTUAL,
                "message": "Past request test.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(TutoringRequest.objects.count(), 0)

        self.assertContains(
            response,
            "The tutoring session must be scheduled "
            "for a future date and time.",
        )

    def test_tutor_cannot_request_tutoring_from_themselves(self):
        self.client.login(
            email=self.tutor_user.email,
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tutoring:request_tutoring",
                args=[self.tutor.id],
            )
        )

        self.assertRedirects(
            response,
            reverse("tutoring:tutor_search"),
        )

        self.assertEqual(
            TutoringRequest.objects.count(),
            0,
        )

    def test_unapproved_tutor_cannot_receive_requests(self):
        unapproved_user = User.objects.create_user(
            email="unapproved@eafit.edu.co",
            password=self.password,
        )

        unapproved_tutor = TutorProfile.objects.create(
            user=unapproved_user,
            is_approved=False,
        )

        unapproved_tutor.subjects.add(self.subject)

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tutoring:request_tutoring",
                args=[unapproved_tutor.id],
            )
        )

        self.assertEqual(response.status_code, 404)
