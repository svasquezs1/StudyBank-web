"""
RF-23 — Public user profile.

Validation criterion: opening an existing user's public profile displays only
the fields defined as public (display name, profile picture, university,
program, member-since date, approved tutor status and shared materials).
"""
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Program, University, User
from materials.models import Course, Material
from tutoring.models import Subject, TutorProfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp()
PASSWORD = "StudyBank-Test-2026"


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PublicUserProfileTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.university = University.objects.create(name="Universidad EAFIT")
        self.program = Program.objects.create(
            name="Systems Engineering",
            university=self.university,
        )
        self.viewer = User.objects.create_user(
            email="viewer@eafit.edu.co",
            password=PASSWORD,
        )
        self.owner = User.objects.create_user(
            email="laura.gomez@eafit.edu.co",
            password=PASSWORD,
            first_name="Laura",
            last_name="Gómez",
            university=self.university,
            program=self.program,
        )
        self.course = Course.objects.create(name="Data Structures")
        self.url = reverse("accounts:public_profile", args=[self.owner.pk])

    def create_material(self, title, user=None):
        return Material.objects.create(
            title=title,
            uploaded_by=user or self.owner,
            course=self.course,
            university=self.university,
            file_type=Material.FileType.SUMMARY,
            file=SimpleUploadedFile(f"{title}.pdf", b"%PDF-1.4", content_type="application/pdf"),
        )

    def login_viewer(self):
        self.client.login(email=self.viewer.email, password=PASSWORD)

    # --- Access ---------------------------------------------------------

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")

    def test_unknown_user_returns_404(self):
        self.login_viewer()

        response = self.client.get(reverse("accounts:public_profile", args=[9999]))

        self.assertEqual(response.status_code, 404)

    def test_inactive_user_returns_404(self):
        self.owner.is_active = False
        self.owner.save()
        self.login_viewer()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    # --- Public fields --------------------------------------------------

    def test_profile_shows_public_fields(self):
        self.login_viewer()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/public_profile.html")
        self.assertContains(response, "Laura Gómez")
        self.assertContains(response, "Universidad EAFIT")
        self.assertContains(response, "Systems Engineering")
        self.assertContains(response, "Member since")

    def test_profile_does_not_expose_private_fields(self):
        self.login_viewer()

        response = self.client.get(self.url)

        self.assertNotContains(response, self.owner.email)
        self.assertNotContains(response, self.owner.password)

    def test_name_falls_back_to_email_prefix_without_full_domain(self):
        unnamed = User.objects.create_user(email="jdoe@eafit.edu.co", password=PASSWORD)
        self.login_viewer()

        response = self.client.get(reverse("accounts:public_profile", args=[unnamed.pk]))

        self.assertContains(response, "jdoe")
        self.assertNotContains(response, "jdoe@eafit.edu.co")
        self.assertContains(response, "University not specified")

    # --- Shared materials -----------------------------------------------

    def test_lists_only_materials_shared_by_this_user(self):
        self.create_material("Graphs summary")
        self.create_material("Someone else's notes", user=self.viewer)
        self.login_viewer()

        response = self.client.get(self.url)

        self.assertContains(response, "Graphs summary")
        self.assertNotContains(response, "Someone else&#x27;s notes")
        self.assertEqual(response.context["shared_materials_total"], 1)

    def test_material_links_to_its_detail_page(self):
        material = self.create_material("Trees cheat sheet")
        self.login_viewer()

        response = self.client.get(self.url)

        self.assertContains(response, reverse("materials:detail", args=[material.pk]))

    def test_shows_empty_message_without_materials(self):
        self.login_viewer()

        response = self.client.get(self.url)

        self.assertContains(response, "has not shared any materials yet")

    def test_limits_listed_materials_and_reports_total(self):
        for number in range(8):
            self.create_material(f"Material {number}")
        self.login_viewer()

        response = self.client.get(self.url)

        self.assertEqual(len(response.context["shared_materials"]), 6)
        self.assertEqual(response.context["shared_materials_total"], 8)
        self.assertContains(response, "Showing the 6 most recent of")

    # --- Tutor status ---------------------------------------------------

    def test_approved_tutor_shows_subjects_and_tutor_profile_link(self):
        tutor = TutorProfile.objects.create(user=self.owner, is_approved=True)
        tutor.subjects.add(Subject.objects.create(name="Calculus 3"))
        self.login_viewer()

        response = self.client.get(self.url)

        self.assertContains(response, "Approved tutor")
        self.assertContains(response, "Calculus 3")
        self.assertContains(response, reverse("tutoring:tutor_profile", args=[tutor.pk]))

    def test_unapproved_tutor_is_not_shown_as_tutor(self):
        tutor = TutorProfile.objects.create(user=self.owner, is_approved=False)
        self.login_viewer()

        response = self.client.get(self.url)

        self.assertIsNone(response.context["approved_tutor"])
        self.assertNotContains(response, "Approved tutor")
        self.assertNotContains(response, reverse("tutoring:tutor_profile", args=[tutor.pk]))

    # --- Own profile and entry points -----------------------------------

    def test_own_profile_shows_edit_button(self):
        self.client.login(email=self.owner.email, password=PASSWORD)

        response = self.client.get(self.url)

        self.assertTrue(response.context["is_own_profile"])
        self.assertContains(response, reverse("accounts:edit_profile"))

    def test_other_user_profile_has_no_edit_button(self):
        self.login_viewer()

        response = self.client.get(self.url)

        self.assertFalse(response.context["is_own_profile"])
        self.assertNotContains(response, "Edit profile")

    def test_edit_profile_page_links_to_own_public_profile(self):
        self.client.login(email=self.owner.email, password=PASSWORD)

        response = self.client.get(reverse("accounts:edit_profile"))

        self.assertContains(response, self.url)

    def test_tutor_profile_links_to_user_public_profile(self):
        tutor = TutorProfile.objects.create(user=self.owner, is_approved=True)
        self.login_viewer()

        response = self.client.get(reverse("tutoring:tutor_profile", args=[tutor.pk]))

        self.assertContains(response, self.url)
        