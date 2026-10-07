from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from tutoring.models import Subject, TutoringRequest, TutorProfile

from .models import Notification


User = get_user_model()


class NotificationTestBase(TestCase):
    def setUp(self):
        self.password = "TestPassword123!"
        self.student = User.objects.create_user(
            email="student@eafit.edu.co", password=self.password
        )
        self.tutor_user = User.objects.create_user(
            email="tutor@eafit.edu.co", password=self.password
        )
        self.subject = Subject.objects.create(name="Calculus")
        self.tutor = TutorProfile.objects.create(
            user=self.tutor_user, is_approved=True
        )
        self.tutor.subjects.add(self.subject)

    def create_request(self):
        return TutoringRequest.objects.create(
            student=self.student,
            tutor=self.tutor,
            subject=self.subject,
            scheduled_at=timezone.now() + timedelta(days=1),
            mode=TutoringRequest.Mode.VIRTUAL,
        )


class NotifyTutorOfNewRequestTests(NotificationTestBase):
    """RF-19: notify the tutor as soon as a request is submitted."""

    def test_new_request_notifies_tutor_immediately(self):
        tutoring_request = self.create_request()

        notifications = Notification.objects.filter(recipient=self.tutor_user)
        self.assertEqual(notifications.count(), 1)
        notification = notifications.first()
        self.assertEqual(notification.tutoring_request, tutoring_request)
        self.assertFalse(notification.is_read)

    def test_message_uses_student_name_and_subject(self):
        self.student.first_name = "Ana"
        self.student.last_name = "Perez"
        self.student.save()

        self.create_request()

        self.assertEqual(
            Notification.objects.get(recipient=self.tutor_user).message,
            "Student Ana Perez has requested a tutoring session for Calculus.",
        )

    def test_message_falls_back_to_email_without_name(self):
        self.create_request()

        self.assertIn(
            "Student student@eafit.edu.co has requested",
            Notification.objects.get(recipient=self.tutor_user).message,
        )

    def test_link_points_to_the_specific_incoming_request(self):
        tutoring_request = self.create_request()

        self.assertEqual(
            Notification.objects.get(recipient=self.tutor_user).link,
            f"{reverse('tutoring:incoming_requests')}#request-{tutoring_request.id}",
        )

    def test_new_request_does_not_notify_student(self):
        self.create_request()

        self.assertFalse(
            Notification.objects.filter(recipient=self.student).exists()
        )

    def test_request_submitted_through_view_notifies_tutor(self):
        self.client.login(email=self.student.email, password=self.password)
        scheduled = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")

        self.client.post(
            reverse("tutoring:request_tutoring", args=[self.tutor.id]),
            {
                "subject": self.subject.id,
                "scheduled_at": scheduled,
                "mode": TutoringRequest.Mode.IN_PERSON,
                "message": "Help with limits",
            },
        )

        self.assertEqual(TutoringRequest.objects.count(), 1)
        self.assertEqual(
            Notification.objects.filter(recipient=self.tutor_user).count(), 1
        )


class NotificationListViewTests(NotificationTestBase):
    def test_list_requires_login(self):
        response = self.client.get(reverse("notifications:list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_user_only_sees_own_notifications(self):
        self.create_request()
        Notification.objects.create(recipient=self.student, message="Other user")
        self.client.login(email=self.tutor_user.email, password=self.password)

        response = self.client.get(reverse("notifications:list"))

        self.assertContains(response, "has requested a tutoring session")
        self.assertNotContains(response, "Other user")

    def test_list_shows_request_details(self):
        tutoring_request = self.create_request()
        tutoring_request.message = "Help with limits"
        tutoring_request.save()
        self.client.login(email=self.tutor_user.email, password=self.password)

        response = self.client.get(reverse("notifications:list"))

        self.assertContains(response, "Virtual")
        self.assertContains(response, "Help with limits")
        self.assertContains(response, f"#request-{tutoring_request.id}")

    def test_opening_list_marks_notifications_as_read(self):
        self.create_request()
        self.client.login(email=self.tutor_user.email, password=self.password)

        self.client.get(reverse("notifications:list"))

        self.assertFalse(
            Notification.objects.filter(
                recipient=self.tutor_user, is_read=False
            ).exists()
        )

    def test_navbar_shows_unread_count(self):
        self.create_request()
        self.client.login(email=self.tutor_user.email, password=self.password)

        response = self.client.get(reverse("home"))

        self.assertContains(response, '<span class="nav-badge">1</span>', html=True)
