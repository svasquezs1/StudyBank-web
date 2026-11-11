"""
Tests for the seed_studybank command, which loads the shared catalogs and the
team administrator accounts.
"""
import os
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from accounts.management.commands.seed_studybank import (
    ADMINS,
    COURSES,
    PROGRAMS,
    SUBJECTS,
    UNIVERSITY,
)
from accounts.models import Program, University, User
from materials.models import Course
from tutoring.models import Subject

PASSWORD = "Seed-StudyBank-2026"
ADMIN_EMAILS = [admin["email"] for admin in ADMINS]


def run_seed(password=PASSWORD, *args):
    output = StringIO()
    with mock.patch.dict(os.environ, {"SEED_ADMIN_PASSWORD": password}):
        call_command("seed_studybank", *args, stdout=output)
    return output.getvalue()


class SeedCommandTests(TestCase):
    def test_creates_catalogs(self):
        run_seed()

        self.assertTrue(University.objects.filter(name=UNIVERSITY).exists())
        self.assertEqual(Program.objects.count(), len(PROGRAMS))
        self.assertEqual(Course.objects.count(), len(COURSES))
        self.assertEqual(Subject.objects.count(), len(SUBJECTS))

    def test_creates_the_three_team_administrators(self):
        run_seed()

        self.assertEqual(
            sorted(ADMIN_EMAILS),
            ["gisel@eafit.edu.co", "samuel@eafit.edu.co", "sebastian@eafit.edu.co"],
        )
        for email in ADMIN_EMAILS:
            with self.subTest(email=email):
                user = User.objects.get(email=email)
                self.assertTrue(user.is_staff)
                self.assertTrue(user.is_superuser)
                self.assertTrue(user.is_active)
                self.assertTrue(user.check_password(PASSWORD))
                self.assertEqual(user.university.name, UNIVERSITY)

    def test_administrators_can_open_the_admin_site(self):
        run_seed()

        self.assertTrue(self.client.login(email="gisel@eafit.edu.co", password=PASSWORD))
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_running_twice_does_not_duplicate_anything(self):
        run_seed()
        output = run_seed()

        self.assertEqual(University.objects.count(), 1)
        self.assertEqual(Program.objects.count(), len(PROGRAMS))
        self.assertEqual(Course.objects.count(), len(COURSES))
        self.assertEqual(Subject.objects.count(), len(SUBJECTS))
        self.assertEqual(User.objects.filter(email__in=ADMIN_EMAILS).count(), 3)
        self.assertIn("already exists (password unchanged)", output)

    def test_keeps_existing_password_unless_reset_is_requested(self):
        run_seed()
        run_seed("Another-Seed-Password-2026")
        self.assertTrue(User.objects.get(email="samuel@eafit.edu.co").check_password(PASSWORD))

        run_seed("Another-Seed-Password-2026", "--reset-admin-passwords")
        self.assertTrue(
            User.objects.get(email="samuel@eafit.edu.co").check_password("Another-Seed-Password-2026")
        )

    def test_existing_regular_user_becomes_administrator_and_keeps_data(self):
        User.objects.create_user(
            email="sebastian@eafit.edu.co", password="Own-Password-2026", first_name="Sebas"
        )

        run_seed()

        user = User.objects.get(email="sebastian@eafit.edu.co")
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.first_name, "Sebas")
        self.assertTrue(user.check_password("Own-Password-2026"))

    def test_reuses_existing_catalog_records(self):
        Course.objects.create(name="Calculus I")
        Subject.objects.create(name="Databases")

        run_seed()

        self.assertEqual(Course.objects.filter(name="Calculus I").count(), 1)
        self.assertEqual(Subject.objects.filter(name="Databases").count(), 1)

    def test_fails_without_password_and_creates_nothing(self):
        with self.assertRaisesMessage(CommandError, "SEED_ADMIN_PASSWORD is not set"):
            run_seed("")

        self.assertFalse(User.objects.exists())
        self.assertFalse(University.objects.exists())

    def test_rejects_a_weak_password(self):
        with self.assertRaisesMessage(CommandError, "SEED_ADMIN_PASSWORD is too weak"):
            run_seed("12345")

        self.assertFalse(User.objects.exists())
