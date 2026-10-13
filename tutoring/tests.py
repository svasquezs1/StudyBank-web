from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Subject,
    TutoringRating,
    TutoringRequest,
    TutorProfile,
)


User = get_user_model()


class TutoringRequestTests(TestCase):
    def setUp(self):
        self.password = "TestPassword123!"

        self.student = User.objects.create_user(
            email="student@eafit.edu.co",
            password=self.password,
        )

        self.other_student = User.objects.create_user(
            email="otherstudent@eafit.edu.co",
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
            message="I need help with Calculus.",
            status=status,
        )

    # =========================================================
    # RF-11 TESTS
    # =========================================================

    def test_authenticated_student_can_request_tutoring(
        self
    ):
        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        scheduled_at = (
            timezone.now()
            + timedelta(days=2)
        )

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

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            TutoringRequest.objects.count(),
            1,
        )

        tutoring_request = (
            TutoringRequest.objects.first()
        )

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
        tutoring_request = self.create_request()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.PENDING,
        )

    def test_past_date_is_rejected(self):
        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        past_date = (
            timezone.now()
            - timedelta(days=1)
        )

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

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            TutoringRequest.objects.count(),
            0,
        )

        self.assertContains(
            response,
            "The tutoring session must be scheduled "
            "for a future date and time.",
        )

    def test_tutor_cannot_request_tutoring_from_themselves(
        self
    ):
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
            reverse(
                "tutoring:tutor_search"
            ),
        )

        self.assertEqual(
            TutoringRequest.objects.count(),
            0,
        )

    def test_unapproved_tutor_cannot_receive_requests(
        self
    ):
        unapproved_user = User.objects.create_user(
            email="unapproved@eafit.edu.co",
            password=self.password,
        )

        unapproved_tutor = (
            TutorProfile.objects.create(
                user=unapproved_user,
                is_approved=False,
            )
        )

        unapproved_tutor.subjects.add(
            self.subject
        )

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

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_successful_request_redirects_to_my_requests(
        self
    ):
        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        scheduled_at = (
            timezone.now()
            + timedelta(days=2)
        )

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

        expected_url = (
            reverse("tutoring:my_requests")
            + "?sent=1"
        )

        self.assertRedirects(
            response,
            expected_url,
        )

    def test_student_can_view_their_requests(self):
        tutoring_request = self.create_request()

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.get(
            reverse("tutoring:my_requests")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            tutoring_request.subject.name,
        )

        self.assertContains(
            response,
            self.tutor_user.email,
        )

        self.assertContains(
            response,
            "Pending",
        )

    def test_tutor_can_view_incoming_requests(self):
        tutoring_request = self.create_request()

        self.client.login(
            email=self.tutor_user.email,
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tutoring:incoming_requests"
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            tutoring_request.student.email,
        )

        self.assertContains(
            response,
            tutoring_request.subject.name,
        )

        self.assertContains(
            response,
            "Pending",
        )

    # =========================================================
    # RF-12 TESTS
    # =========================================================

    def test_tutor_can_accept_pending_request(self):
        tutoring_request = self.create_request()

        self.client.login(
            email=self.tutor_user.email,
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tutoring:accept_request",
                args=[tutoring_request.id],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "tutoring:incoming_requests"
            ),
        )

        tutoring_request.refresh_from_db()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.ACCEPTED,
        )

    def test_tutor_can_reject_pending_request(self):
        tutoring_request = self.create_request()

        self.client.login(
            email=self.tutor_user.email,
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tutoring:reject_request",
                args=[tutoring_request.id],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "tutoring:incoming_requests"
            ),
        )

        tutoring_request.refresh_from_db()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.REJECTED,
        )

    def test_non_tutor_cannot_manage_request(self):
        tutoring_request = self.create_request()

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tutoring:accept_request",
                args=[tutoring_request.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        tutoring_request.refresh_from_db()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.PENDING,
        )

    def test_other_tutor_cannot_manage_request(self):
        other_tutor_user = User.objects.create_user(
            email="othertutor@eafit.edu.co",
            password=self.password,
        )

        other_tutor = TutorProfile.objects.create(
            user=other_tutor_user,
            is_approved=True,
        )

        other_tutor.subjects.add(
            self.subject
        )

        tutoring_request = self.create_request()

        self.client.login(
            email=other_tutor_user.email,
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tutoring:reject_request",
                args=[tutoring_request.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

        tutoring_request.refresh_from_db()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.PENDING,
        )

    def test_decided_request_cannot_be_changed_again(
        self
    ):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.ACCEPTED,
        )

        self.client.login(
            email=self.tutor_user.email,
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tutoring:reject_request",
                args=[tutoring_request.id],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "tutoring:incoming_requests"
            ),
        )

        tutoring_request.refresh_from_db()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.ACCEPTED,
        )

    # =========================================================
    # RF-17 TESTS
    # =========================================================

    def test_tutor_can_mark_accepted_session_as_completed(
        self
    ):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.ACCEPTED,
        )

        self.client.login(
            email=self.tutor_user.email,
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tutoring:complete_request",
                args=[tutoring_request.id],
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "tutoring:incoming_requests"
            ),
        )

        tutoring_request.refresh_from_db()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.COMPLETED,
        )

    def test_pending_session_cannot_be_marked_completed(
        self
    ):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.PENDING,
        )

        self.client.login(
            email=self.tutor_user.email,
            password=self.password,
        )

        self.client.post(
            reverse(
                "tutoring:complete_request",
                args=[tutoring_request.id],
            )
        )

        tutoring_request.refresh_from_db()

        self.assertEqual(
            tutoring_request.status,
            TutoringRequest.Status.PENDING,
        )

    def test_completed_session_shows_rate_session_button(
        self
    ):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.COMPLETED,
        )

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tutoring:my_requests"
            )
        )

        self.assertContains(
            response,
            "Rate session",
        )

        self.assertContains(
            response,
            reverse(
                "tutoring:rate_request",
                args=[tutoring_request.id],
            ),
        )

    def test_accepted_session_does_not_show_rating_button(
        self
    ):
        self.create_request(
            status=TutoringRequest.Status.ACCEPTED,
        )

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tutoring:my_requests"
            )
        )

        self.assertNotContains(
            response,
            "Rate session",
        )

    def test_student_can_rate_completed_session(
        self
    ):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.COMPLETED,
        )

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tutoring:rate_request",
                args=[tutoring_request.id],
            ),
            {
                "score": 5,
                "feedback": (
                    "Excellent tutoring session."
                ),
            },
        )

        expected_url = (
            reverse(
                "tutoring:my_requests"
            )
            + "?rated=1"
        )

        self.assertRedirects(
            response,
            expected_url,
        )

        self.assertEqual(
            TutoringRating.objects.count(),
            1,
        )

        rating = TutoringRating.objects.first()

        self.assertEqual(
            rating.tutoring_request,
            tutoring_request,
        )

        self.assertEqual(
            rating.student,
            self.student,
        )

        self.assertEqual(
            rating.tutor,
            self.tutor,
        )

        self.assertEqual(
            rating.score,
            5,
        )

        self.assertEqual(
            rating.feedback,
            "Excellent tutoring session.",
        )

    def test_other_student_cannot_rate_session(
        self
    ):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.COMPLETED,
        )

        self.client.login(
            email=self.other_student.email,
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tutoring:rate_request",
                args=[tutoring_request.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_non_completed_session_cannot_be_rated(
        self
    ):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.ACCEPTED,
        )

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tutoring:rate_request",
                args=[tutoring_request.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_rating_must_be_between_one_and_five(
        self
    ):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.COMPLETED,
        )

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tutoring:rate_request",
                args=[tutoring_request.id],
            ),
            {
                "score": 6,
                "feedback": "Invalid rating.",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            TutoringRating.objects.count(),
            0,
        )

    def test_rating_cannot_be_submitted_twice(
        self
    ):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.COMPLETED,
        )

        TutoringRating.objects.create(
            tutoring_request=tutoring_request,
            student=self.student,
            tutor=self.tutor,
            score=5,
            feedback="Excellent.",
        )

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.post(
            reverse(
                "tutoring:rate_request",
                args=[tutoring_request.id],
            ),
            {
                "score": 1,
                "feedback": "Second rating.",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            TutoringRating.objects.count(),
            1,
        )

        rating = TutoringRating.objects.get(
            tutoring_request=tutoring_request
        )

        self.assertEqual(
            rating.score,
            5,
        )

        self.assertContains(
            response,
            "already been rated",
        )

    def test_existing_rating_is_read_only(
        self
    ):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.COMPLETED,
        )

        TutoringRating.objects.create(
            tutoring_request=tutoring_request,
            student=self.student,
            tutor=self.tutor,
            score=4,
            feedback="Very helpful.",
        )

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tutoring:rate_request",
                args=[tutoring_request.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "4 / 5",
        )

        self.assertContains(
            response,
            "Very helpful.",
        )

        self.assertContains(
            response,
            "already been rated",
        )

        self.assertNotContains(
            response,
            "Submit rating",
        )

    def test_tutor_average_rating_is_calculated_dynamically(
        self
    ):
        first_request = self.create_request(
            status=TutoringRequest.Status.COMPLETED,
        )

        second_student = User.objects.create_user(
            email="secondstudent@eafit.edu.co",
            password=self.password,
        )

        second_request = (
            TutoringRequest.objects.create(
                student=second_student,
                tutor=self.tutor,
                subject=self.subject,
                scheduled_at=(
                    timezone.now()
                    + timedelta(days=3)
                ),
                mode=TutoringRequest.Mode.VIRTUAL,
                status=TutoringRequest.Status.COMPLETED,
            )
        )

        TutoringRating.objects.create(
            tutoring_request=first_request,
            student=self.student,
            tutor=self.tutor,
            score=5,
        )

        TutoringRating.objects.create(
            tutoring_request=second_request,
            student=second_student,
            tutor=self.tutor,
            score=3,
        )

        self.assertEqual(
            self.tutor.average_rating,
            4.0,
        )

        self.assertEqual(
            self.tutor.ratings_count,
            2,
        )

    def test_rating_success_message_is_displayed(
        self
    ):
        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        response = self.client.get(
            reverse(
                "tutoring:my_requests"
            )
            + "?rated=1"
        )

        self.assertContains(
            response,
            "Thank you for rating your tutoring session!",
        )
