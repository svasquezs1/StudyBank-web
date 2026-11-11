"""
Feedback messages for registration (RF-01), login (RF-02) and logout (RF-21).

Successful actions show a confirmation message. Failed actions show one generic
message that is identical for every cause, so the page never reveals whether an
email is registered, which field was wrong or why a password was rejected.
"""
from django.contrib.auth import get_user
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from accounts.auth_views import LOGIN_ERROR_MESSAGE, LOGOUT_SUCCESS_MESSAGE
from accounts.models import Program, University, User
from accounts.views import REGISTER_ERROR_MESSAGE, REGISTER_SUCCESS_MESSAGE

PASSWORD = "StudyBank-Test-2026"

# Texts that would reveal the cause of an error. None of them may appear.
REVEALING_TEXTS = [
    "already exists",
    "You must use an institutional email",
    "too short",
    "too common",
    "entirely numeric",
    "too similar",
    "didn’t match",
    "didn't match",
    "This field is required",
    "Please enter a correct",
    "This account is inactive",
]


def page_messages(response):
    return [str(message) for message in get_messages(response.wsgi_request)]


class AuthMessagesTestCase(TestCase):
    def setUp(self):
        self.university = University.objects.create(name="Universidad EAFIT")
        self.program = Program.objects.create(name="Systems Engineering", university=self.university)
        self.user = User.objects.create_user(
            email="existing@eafit.edu.co",
            password=PASSWORD,
            first_name="Laura",
        )

    def assert_reveals_nothing(self, response):
        content = response.content.decode()
        for text in REVEALING_TEXTS:
            self.assertNotIn(text, content, f"The page reveals the cause of the error: {text!r}")


class RegistrationMessagesTests(AuthMessagesTestCase):
    url = reverse("accounts:register")

    def registration_data(self, **overrides):
        data = {
            "email": "new.student@eafit.edu.co",
            "university": self.university.pk,
            "program": self.program.pk,
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_successful_registration_shows_message_on_home(self):
        response = self.client.post(self.url, self.registration_data(), follow=True)

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, REGISTER_SUCCESS_MESSAGE)
        self.assertTrue(get_user(self.client).is_authenticated)

    def test_every_registration_error_shows_the_same_generic_message(self):
        invalid_cases = {
            "email already registered": {"email": "existing@eafit.edu.co"},
            "non-institutional email": {"email": "student@gmail.com"},
            "empty email": {"email": ""},
            "short password": {"password1": "abc", "password2": "abc"},
            "numeric password": {"password1": "12345678901", "password2": "12345678901"},
            "common password": {"password1": "password123", "password2": "password123"},
            "passwords do not match": {"password2": "Another-Password-2026"},
            "missing university and program": {"university": "", "program": ""},
        }
        for case, overrides in invalid_cases.items():
            with self.subTest(case=case):
                response = self.client.post(self.url, self.registration_data(**overrides))

                self.assertEqual(response.status_code, 200)
                self.assertEqual(page_messages(response), [REGISTER_ERROR_MESSAGE])
                self.assert_reveals_nothing(response)

    def test_registered_and_new_email_errors_look_identical(self):
        weak = {"password1": "abc", "password2": "abc"}
        existing = self.client.post(self.url, self.registration_data(email="existing@eafit.edu.co", **weak))
        new = self.client.post(self.url, self.registration_data(email="nobody@eafit.edu.co", **weak))

        self.assertEqual(page_messages(existing), page_messages(new))

    def test_failed_registration_keeps_email_but_not_passwords(self):
        response = self.client.post(self.url, self.registration_data(password2="Different-2026"))

        self.assertContains(response, 'value="new.student@eafit.edu.co"')
        self.assertNotContains(response, PASSWORD)

    def test_requirements_are_always_visible(self):
        response = self.client.get(self.url)

        self.assertContains(response, "Requirements")
        self.assertContains(response, "@eafit.edu.co")
        self.assertContains(response, "at least 8 characters")
        self.assertEqual(page_messages(response), [])


class LoginMessagesTests(AuthMessagesTestCase):
    url = reverse("accounts:login")

    def test_successful_login_shows_welcome_message(self):
        response = self.client.post(
            self.url,
            {"username": "existing@eafit.edu.co", "password": PASSWORD},
            follow=True,
        )

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "Welcome back, Laura!")

    def test_welcome_message_uses_email_prefix_without_name(self):
        User.objects.create_user(email="jdoe@eafit.edu.co", password=PASSWORD)

        response = self.client.post(
            self.url, {"username": "jdoe@eafit.edu.co", "password": PASSWORD}, follow=True
        )

        self.assertContains(response, "Welcome back, jdoe!")
        self.assertNotContains(response, "Welcome back, jdoe@eafit.edu.co")

    def test_every_login_error_shows_the_same_generic_message(self):
        inactive = User.objects.create_user(email="inactive@eafit.edu.co", password=PASSWORD)
        inactive.is_active = False
        inactive.save()
        invalid_cases = {
            "wrong password": {"username": "existing@eafit.edu.co", "password": "Wrong-2026"},
            "unregistered email": {"username": "nobody@eafit.edu.co", "password": PASSWORD},
            "inactive account": {"username": "inactive@eafit.edu.co", "password": PASSWORD},
            "empty password": {"username": "existing@eafit.edu.co", "password": ""},
            "empty fields": {"username": "", "password": ""},
        }
        for case, data in invalid_cases.items():
            with self.subTest(case=case):
                response = self.client.post(self.url, data)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(page_messages(response), [LOGIN_ERROR_MESSAGE])
                self.assertFalse(get_user(self.client).is_authenticated)
                self.assert_reveals_nothing(response)

    def test_failed_login_does_not_show_the_password(self):
        response = self.client.post(
            self.url, {"username": "existing@eafit.edu.co", "password": "Secret-Typed-2026"}
        )

        self.assertNotContains(response, "Secret-Typed-2026")

    def test_logged_in_user_is_redirected_from_login(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("home"))


class LogoutMessagesTests(AuthMessagesTestCase):
    def test_logout_shows_confirmation_message(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:logout"), follow=True)

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, LOGOUT_SUCCESS_MESSAGE)
        self.assertFalse(get_user(self.client).is_authenticated)

