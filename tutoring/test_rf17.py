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


class TutoringRatingTests(TestCase):
    def setUp(self):
        self.password = "TestPassword123!"

        self.student = User.objects.create_user(
            email="ratingstudent@eafit.edu.co",
            password=self.password,
        )

        self.other_student = User.objects.create_user(
            email="otherratingstudent@eafit.edu.co",
            password=self.password,
        )

        self.tutor_user = User.objects.create_user(
            email="ratingtutor@eafit.edu.co",
            password=self.password,
        )

        self.subject = Subject.objects.create(
            name="Calculus Rating",
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
        student=None,
    ):
        return TutoringRequest.objects.create(
            student=student or self.student,
            tutor=self.tutor,
            subject=self.subject,
            scheduled_at=(
                timezone.now()
                + timedelta(days=2)
            ),
            mode=TutoringRequest.Mode.VIRTUAL,
            message="Rating test.",
            status=status,
        )

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
        tutoring_request = self.create_request()

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

    def test_student_can_rate_completed_session(self):
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
                "feedback": "Excellent tutoring session.",
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

        rating = TutoringRating.objects.get()

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

    def test_other_student_cannot_rate_session(self):
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

    def test_non_completed_session_cannot_be_rated(self):
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

    def test_rating_must_be_between_one_and_five(self):
        tutoring_request = self.create_request(
            status=TutoringRequest.Status.COMPLETED,
        )

        self.client.login(
            email=self.student.email,
            password=self.password,
        )

        self.client.post(
            reverse(
                "tutoring:rate_request",
                args=[tutoring_request.id],
            ),
            {
                "score": 6,
                "feedback": "Invalid.",
            },
        )

        self.assertEqual(
            TutoringRating.objects.count(),
            0,
        )

    def test_rating_cannot_be_submitted_twice(self):
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
            TutoringRating.objects.count(),
            1,
        )

        self.assertContains(
            response,
            "already been rated",
        )

    def test_existing_rating_is_read_only(self):
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

        self.assertContains(
            response,
            "4 / 5",
        )

        self.assertContains(
            response,
            "Very helpful.",
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
            email="secondratingstudent@eafit.edu.co",
            password=self.password,
        )

        second_request = self.create_request(
            status=TutoringRequest.Status.COMPLETED,
            student=second_student,
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

    def test_rating_success_message_is_displayed(self):
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
