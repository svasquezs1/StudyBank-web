"""
Tests for SEC-01: uploaded files under /media/ are only available to logged-in
users (study materials and profile pictures).
"""
import importlib
import shutil
import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import clear_url_caches

import config.urls
from accounts.models import User

MEDIA_DIR = tempfile.mkdtemp(prefix='studybank-media-tests-')
PDF_BYTES = b'%PDF-1.4 StudyBank test material'
PNG_BYTES = b'\x89PNG\r\n\x1a\n test picture'


def reload_urls():
    importlib.reload(config.urls)
    clear_url_caches()


@override_settings(MEDIA_ROOT=MEDIA_DIR, SERVE_MEDIA=True)
class ProtectedMediaTests(TestCase):
    material_url = '/media/materials/calculus-notes.pdf'
    picture_url = '/media/profile_pictures/avatar.png'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(MEDIA_DIR)
        (root / 'materials').mkdir(parents=True, exist_ok=True)
        (root / 'profile_pictures').mkdir(parents=True, exist_ok=True)
        (root / 'materials' / 'calculus-notes.pdf').write_bytes(PDF_BYTES)
        (root / 'profile_pictures' / 'avatar.png').write_bytes(PNG_BYTES)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_DIR, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        reload_urls()
        self.addCleanup(reload_urls)
        self.user = User.objects.create_user(
            email='student@eafit.edu.co', password='Media-Test-2026'
        )

    def login(self):
        self.client.login(email='student@eafit.edu.co', password='Media-Test-2026')

    def test_anonymous_user_cannot_open_a_material_file(self):
        response = self.client.get(self.material_url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
        self.assertIn('next=/media/materials/calculus-notes.pdf', response.url)

    def test_anonymous_user_cannot_open_a_profile_picture(self):
        response = self.client.get(self.picture_url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_logged_in_user_can_open_a_material_file(self):
        self.login()

        response = self.client.get(self.material_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), PDF_BYTES)
        self.assertEqual(response['Cache-Control'], 'private, max-age=3600')

    def test_logged_in_user_can_open_a_profile_picture(self):
        self.login()

        response = self.client.get(self.picture_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), PNG_BYTES)

    def test_missing_file_returns_404(self):
        self.login()

        response = self.client.get('/media/materials/does-not-exist.pdf')

        self.assertEqual(response.status_code, 404)

    def test_paths_outside_the_media_folder_are_not_served(self):
        self.login()

        for path in ['/media/../manage.py', '/media/materials/../../manage.py', '/media/']:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertIn(response.status_code, (400, 404))

    def test_login_redirects_back_to_the_file(self):
        response = self.client.post(
            '/accounts/login/?next=' + self.material_url,
            {'username': 'student@eafit.edu.co', 'password': 'Media-Test-2026'},
        )

        self.assertRedirects(response, self.material_url, fetch_redirect_response=False)
