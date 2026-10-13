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


class TutorDirectorySortingTests(TestCase):
    def setUp(self):
        self.password = "TestPassword123!"

        self.student = User.objects.create_user(
            email="student.rf18@eafit.edu.co",
            password=self.password,
        )

        self.calculus = Subject.objects.create(
            name="Calculus RF18",
        )

        self.programming = Subject.objects.create(
            name="Programming RF18",
        )

        self.tutor_high_user = User.objects.create_user(
            email="high@eafit.edu.co",
            password=self.password,
        )

        self.tutor_high = TutorProfile.objects.create(
            user=self.tutor_high_user,
            is_approved=True,
        )

        self.tutor_high.subjects.add(
            self.calculus
        )

        self.tutor_mid_user = User.objects.create_user(
            email="mid@eafit.edu.co",
            password=self.password,
        )

        self.tutor_mid = TutorProfile.objects.create(
            user=self.tutor_mid_user,
            is_approved=True,
        )

        self.tutor_mid.subjects.add(
            self.calculus,
            self.programming,
        )

        self.tutor_unrated_user = User.objects.create_user(
            email="unrated@eafit.edu.co",
            password=self.password,
        )

        self.tutor_unrated = TutorProfile.objects.create(
            user=self.tutor_unrated_user,
            is_approved=True,
        )

        self.tutor_unrated.subjects.add(
            self.programming
        )

    def create_rating(
        self,
        tutor,
        score,
        index,
    ):
        rating_student = User.objects.create_user(
            email=f"ratingstudent{index}@eafit.edu.co",
            password=self.password,
        )

        tutoring_request = TutoringRequest.objects.create(
            student=rating_student,
            tutor=tutor,
            subject=(
                tutor.subjects.first()
            ),
            scheduled_at=(
                timezone.now()
                - timedelta(days=index + 1)
            ),
            mode=TutoringRequest.Mode.VIRTUAL,
            status=TutoringRequest.Status.COMPLETED,
        )

        return TutoringRating.objects.create(
            tutoring_request=tutoring_request,
            student=rating_student,
            tutor=tutor,
            score=score,
        )

    def login_student(self):
        self.client.login(
            email=self.student.email,
            password=self.password,
        )

    def get_tutor_emails(self, response):
        return [
            tutor.user.email
            for tutor in response.context["tutors"]
        ]

    def test_tutor_directory_requires_authentication(self):
        response = self.client.get(
            reverse("tutoring:tutor_search")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_sort_control_contains_expected_options(self):
        self.login_student()

        response = self.client.get(
            reverse("tutoring:tutor_search")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Sort by",
        )

        self.assertContains(
            response,
            "Highest Rating",
        )

        self.assertContains(
            response,
            "Most Popular",
        )

        self.assertContains(
            response,
            "Alphabetical",
        )

    def test_highest_rating_sorts_descending_and_unrated_last(
        self
    ):
        self.create_rating(
            self.tutor_high,
            5,
            1,
        )

        self.create_rating(
            self.tutor_mid,
            3,
            2,
        )

        self.login_student()

        response = self.client.get(
            reverse("tutoring:tutor_search"),
            {
                "sort": "rating",
            },
        )

        tutor_emails = self.get_tutor_emails(
            response
        )

        self.assertEqual(
            tutor_emails,
            [
                "high@eafit.edu.co",
                "mid@eafit.edu.co",
                "unrated@eafit.edu.co",
            ],
        )

    def test_rating_tie_is_broken_by_review_count(self):
        self.create_rating(
            self.tutor_high,
            5,
            1,
        )

        self.create_rating(
            self.tutor_high,
            3,
            2,
        )

        self.create_rating(
            self.tutor_mid,
            4,
            3,
        )

        self.login_student()

        response = self.client.get(
            reverse("tutoring:tutor_search"),
            {
                "sort": "rating",
            },
        )

        tutor_emails = self.get_tutor_emails(
            response
        )

        self.assertEqual(
            tutor_emails[0],
            "high@eafit.edu.co",
        )

        self.assertEqual(
            tutor_emails[1],
            "mid@eafit.edu.co",
        )

    def test_most_popular_sorts_by_review_count(self):
        self.create_rating(
            self.tutor_high,
            5,
            1,
        )

        self.create_rating(
            self.tutor_mid,
            4,
            2,
        )

        self.create_rating(
            self.tutor_mid,
            5,
            3,
        )

        self.login_student()

        response = self.client.get(
            reverse("tutoring:tutor_search"),
            {
                "sort": "popular",
            },
        )

        tutor_emails = self.get_tutor_emails(
            response
        )

        self.assertEqual(
            tutor_emails[0],
            "mid@eafit.edu.co",
        )

        self.assertEqual(
            tutor_emails[1],
            "high@eafit.edu.co",
        )

    def test_alphabetical_sort_orders_by_email(self):
        self.login_student()

        response = self.client.get(
            reverse("tutoring:tutor_search"),
            {
                "sort": "alphabetical",
            },
        )

        tutor_emails = self.get_tutor_emails(
            response
        )

        self.assertEqual(
            tutor_emails,
            [
                "high@eafit.edu.co",
                "mid@eafit.edu.co",
                "unrated@eafit.edu.co",
            ],
        )

    def test_rating_sort_works_with_subject_filter(self):
        self.create_rating(
            self.tutor_high,
            5,
            1,
        )

        self.create_rating(
            self.tutor_mid,
            4,
            2,
        )

        self.login_student()

        response = self.client.get(
            reverse("tutoring:tutor_search"),
            {
                "subject": str(
                    self.programming.id
                ),
                "sort": "rating",
            },
        )

        tutor_emails = self.get_tutor_emails(
            response
        )

        self.assertEqual(
            tutor_emails,
            [
                "mid@eafit.edu.co",
                "unrated@eafit.edu.co",
            ],
        )

        self.assertEqual(
            response.context[
                "selected_subject"
            ],
            str(self.programming.id),
        )

        self.assertEqual(
            response.context[
                "selected_sort"
            ],
            "rating",
        )

    def test_rating_sort_works_with_search_query(self):
        self.create_rating(
            self.tutor_high,
            5,
            1,
        )

        self.create_rating(
            self.tutor_mid,
            4,
            2,
        )

        self.login_student()

        response = self.client.get(
            reverse("tutoring:tutor_search"),
            {
                "q": "mid",
                "sort": "rating",
            },
        )

        tutor_emails = self.get_tutor_emails(
            response
        )

        self.assertEqual(
            tutor_emails,
            [
                "mid@eafit.edu.co",
            ],
        )

        self.assertEqual(
            response.context[
                "search_query"
            ],
            "mid",
        )

        self.assertEqual(
            response.context[
                "selected_sort"
            ],
            "rating",
        )
        