"""
Automated tests for the accounts app.

Covers RF-01 (registration), RF-02 (login), RF-03 (profile editing),
RF-21 (logout), RNF-04 (password hashing) and RNF-05 (restricted access).
"""
import io
import shutil
import tempfile

from django.contrib.auth import get_user
from django.contrib.auth.hashers import identify_hasher
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import Program, University, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp()
PASSWORD = "StudyBank-Test-2026"


def png_upload(name="avatar.png"):
    """Return a small valid PNG image ready to be sent in a form."""
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color=(224, 164, 88)).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class AccountsTestCase(TestCase):
    def setUp(self):
        self.university = University.objects.create(name="Universidad EAFIT")
        self.program = Program.objects.create(
            name="Systems Engineering",
            university=self.university,
        )

    def create_user(self, email="student@eafit.edu.co", **extra):
        return User.objects.create_user(email=email, password=PASSWORD, **extra)


class UserModelTests(AccountsTestCase):
    def test_create_user_hashes_password_and_uses_email_as_identifier(self):
        user = self.create_user()

        self.assertEqual(User.USERNAME_FIELD, "email")
        self.assertEqual(str(user), "student@eafit.edu.co")
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(user.is_staff)

    def test_create_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password=PASSWORD)

    def test_create_superuser_sets_admin_flags(self):
        admin = User.objects.create_superuser(email="admin@eafit.edu.co", password=PASSWORD)

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_non_institutional_email_fails_model_validation(self):
        user = User(email="student@gmail.com")
        user.set_password(PASSWORD)

        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_program_string_includes_university(self):
        self.assertEqual(str(self.program), "Systems Engineering (Universidad EAFIT)")


class RegistrationTests(AccountsTestCase):
    """RF-01 — User registration with a unique @eafit.edu.co email."""

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

    def test_register_page_loads(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    def test_valid_registration_creates_account_and_logs_in(self):
        response = self.client.post(self.url, self.registration_data())

        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(email="new.student@eafit.edu.co")
        self.assertEqual(user.university, self.university)
        self.assertEqual(user.program, self.program)
        self.assertEqual(get_user(self.client).pk, user.pk)

    def test_non_institutional_email_is_rejected(self):
        response = self.client.post(self.url, self.registration_data(email="student@gmail.com"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["email"])
        self.assertFalse(User.objects.filter(email="student@gmail.com").exists())

    def test_duplicate_email_is_rejected(self):
        self.create_user(email="new.student@eafit.edu.co")

        response = self.client.post(self.url, self.registration_data())

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["email"])
        self.assertEqual(User.objects.filter(email="new.student@eafit.edu.co").count(), 1)

    def test_password_confirmation_must_match(self):
        response = self.client.post(
            self.url,
            self.registration_data(password2="Another-Password-2026"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="new.student@eafit.edu.co").exists())

    def test_university_and_program_are_required(self):
        response = self.client.post(self.url, self.registration_data(university="", program=""))

        form = response.context["form"]
        self.assertIn("university", form.errors)
        self.assertIn("program", form.errors)
        self.assertFalse(User.objects.exists())

    def test_authenticated_user_is_redirected_home(self):
        self.client.force_login(self.create_user())

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse("home"))


class LoginTests(AccountsTestCase):
    """RF-02 — Login with institutional email and password."""

    url = reverse("accounts:login")

    def setUp(self):
        super().setUp()
        self.user = self.create_user()

    def test_login_page_loads(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_valid_credentials_start_a_session(self):
        response = self.client.post(
            self.url,
            {"username": self.user.email, "password": PASSWORD},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertEqual(get_user(self.client).pk, self.user.pk)

    def test_wrong_password_does_not_start_a_session(self):
        response = self.client.post(
            self.url,
            {"username": self.user.email, "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_unknown_email_does_not_start_a_session(self):
        self.client.post(
            self.url,
            {"username": "nobody@eafit.edu.co", "password": PASSWORD},
        )

        self.assertFalse(get_user(self.client).is_authenticated)

    def test_inactive_user_cannot_log_in(self):
        self.user.is_active = False
        self.user.save()

        self.client.post(self.url, {"username": self.user.email, "password": PASSWORD})

        self.assertFalse(get_user(self.client).is_authenticated)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class EditProfileTests(AccountsTestCase):
    """RF-03 — Profile editing (name, university, program, picture)."""

    url = reverse("accounts:edit_profile")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.user = self.create_user()
        self.client.force_login(self.user)
        self.other_university = University.objects.create(name="Universidad Nacional")
        self.other_program = Program.objects.create(
            name="Industrial Engineering",
            university=self.other_university,
        )

    def profile_data(self, **overrides):
        data = {
            "first_name": "Ana",
            "last_name": "Restrepo",
            "university": self.other_university.pk,
            "program": self.other_program.pk,
        }
        data.update(overrides)
        return data

    def test_edit_profile_page_loads_with_current_data(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/edit_profile.html")
        self.assertEqual(response.context["form"].instance, self.user)

    def test_valid_changes_are_saved_and_shown_on_next_load(self):
        response = self.client.post(self.url, self.profile_data(), follow=True)

        self.assertRedirects(response, self.url)
        self.assertContains(response, "Profile updated successfully.")
        self.user.refresh_from_db()
        self.assertEqual(self.user.get_full_name(), "Ana Restrepo")
        self.assertEqual(self.user.university, self.other_university)
        self.assertEqual(self.user.program, self.other_program)

        next_load = self.client.get(self.url)
        self.assertContains(next_load, 'value="Ana"')
        self.assertContains(next_load, 'value="Restrepo"')

    def test_valid_profile_picture_is_stored(self):
        self.client.post(self.url, self.profile_data(profile_picture=png_upload()))

        self.user.refresh_from_db()
        self.assertTrue(self.user.profile_picture.name.startswith("profile_pictures/"))

    def test_file_with_disallowed_extension_is_rejected(self):
        text_file = SimpleUploadedFile("avatar.txt", b"not an image", content_type="text/plain")

        response = self.client.post(self.url, self.profile_data(profile_picture=text_file))

        self.assertEqual(response.status_code, 200)
        self.assertIn("profile_picture", response.context["form"].errors)
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_picture)

    def test_editing_does_not_change_the_email(self):
        self.client.post(self.url, self.profile_data(email="changed@eafit.edu.co"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "student@eafit.edu.co")


class LogoutTests(AccountsTestCase):
    """RF-21 — Logout invalidates the session."""

    url = reverse("accounts:logout")

    def setUp(self):
        super().setUp()
        self.client.force_login(self.create_user())

    def test_post_logout_ends_the_session(self):
        response = self.client.post(self.url)

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(get_user(self.client).is_authenticated)

    def test_protected_view_requires_login_again_after_logout(self):
        self.client.post(self.url)

        response = self.client.get(reverse("accounts:edit_profile"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:edit_profile')}",
        )

    def test_get_logout_is_not_allowed(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(get_user(self.client).is_authenticated)


class PasswordStorageTests(AccountsTestCase):
    """RNF-04 — Passwords are stored with Django's PBKDF2 hasher."""

    def test_password_is_stored_with_pbkdf2(self):
        user = self.create_user()

        self.assertEqual(identify_hasher(user.password).algorithm, "pbkdf2_sha256")
        self.assertNotIn(PASSWORD, user.password)

    def test_registration_stores_hashed_password(self):
        self.client.post(
            reverse("accounts:register"),
            {
                "email": "hashed@eafit.edu.co",
                "university": self.university.pk,
                "program": self.program.pk,
                "password1": PASSWORD,
                "password2": PASSWORD,
            },
        )

        user = User.objects.get(email="hashed@eafit.edu.co")
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))


class RestrictedAccessTests(TestCase):
    """RNF-05 — Protected views redirect anonymous users to the login page."""

    PROTECTED_URLS = [
        ("accounts:edit_profile", []),
        ("accounts:public_profile", [1]),
        ("materials:list", []),
        ("materials:search_materials", []),
        ("materials:upload", []),
        ("materials:detail", [1]),
        ("materials:download", [1]),
        ("materials:edit", [1]),
        ("materials:rate", [1]),
        ("tutoring:register_tutor", []),
        ("tutoring:tutor_search", []),
        ("tutoring:tutor_profile", [1]),
        ("tutoring:availability", []),
        ("tutoring:edit_availability", [1]),
        ("tutoring:delete_availability", [1]),
        ("tutoring:request_tutoring", [1]),
        ("tutoring:my_requests", []),
        ("tutoring:statistics", []),
        ("tutoring:incoming_requests", []),
        ("tutoring:accept_request", [1]),
        ("tutoring:reject_request", [1]),
        ("tutoring:cancel_request", [1]),
        ("tutoring:complete_request", [1]),
        ("tutoring:rate_request", [1]),
        ("notifications:list", []),
    ]

    def test_anonymous_requests_are_redirected_to_login(self):
        login_url = reverse("accounts:login")

        for name, args in self.PROTECTED_URLS:
            url = reverse(name, args=args)
            with self.subTest(view=name):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{login_url}?next={url}",
                    fetch_redirect_response=False,
                )

    def test_public_pages_do_not_require_login(self):
        for name in ("home", "accounts:login", "accounts:register"):
            with self.subTest(view=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)