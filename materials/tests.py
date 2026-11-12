from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, University, Program
from materials.models import Material, Course
from django.contrib.messages import get_messages

class MaterialDetailAndDownloadTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(name="EAFIT")
        self.program = Program.objects.create(name="Ingeniería de Sistemas", university=self.university)
        self.user = User.objects.create_user(
            email="testuser@eafit.edu.co",
            password="Password123!",
            university=self.university,
            program=self.program
        )
        self.course = Course.objects.create(name="Software Engineering")
        self.fake_file = SimpleUploadedFile("test_doc.pdf", b"file content stream", content_type="application/pdf")
        
        self.material = Material.objects.create(
            title="Partial Exam Summary",
            description="Detailed review notes for first exam",
            uploaded_by=self.user,
            course=self.course,
            university=self.university,
            file_type="summary",
            file=self.fake_file
        )

    def test_unauthenticated_user_redirected_on_detail_and_download(self):
        """Redirige a usuarios no autenticados en la vista de detalles y en la descarga"""
        detail_url = reverse('materials:detail', kwargs={'pk': self.material.pk})
        download_url = reverse('materials:download', kwargs={'pk': self.material.pk})
        
        res_detail = self.client.get(detail_url)
        res_download = self.client.get(download_url)

        self.assertRedirects(res_detail, f"/accounts/login/?next={detail_url}")
        self.assertRedirects(res_download, f"/accounts/login/?next={download_url}")

    def test_authenticated_download_serves_file_with_content_disposition(self):
        """Usuario autenticado descarga directamente el archivo con cabeceras de adjunto"""
        self.client.login(email="testuser@eafit.edu.co", password="Password123!")
        url = reverse('materials:download', kwargs={'pk': self.material.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.has_header('Content-Disposition'))
        self.assertIn('attachment;', response['Content-Disposition'])

    def test_missing_file_shows_error_message(self):
        """Si el archivo en disco no existe, muestra un mensaje de error sin romper la app"""
        self.client.login(email="testuser@eafit.edu.co", password="Password123!")
        # Eliminamos la referencia física del archivo
        self.material.file.delete(save=False)
        
        url = reverse('materials:download', kwargs={'pk': self.material.pk})
        response = self.client.get(url, follow=True)
        
        self.assertContains(response, "The requested file no longer exists")

class MaterialEditTests(TestCase):
    """RF-24: edición de materiales por el uploader."""

    def setUp(self):
        self.university = University.objects.create(name="EAFIT")
        self.other_university = University.objects.create(name="UdeA")
        self.program = Program.objects.create(name="Ingeniería de Sistemas", university=self.university)
        self.owner = User.objects.create_user(
            email="owner@eafit.edu.co", password="Password123!",
            university=self.university, program=self.program,
        )
        self.other = User.objects.create_user(
            email="other@eafit.edu.co", password="Password123!",
            university=self.university, program=self.program,
        )
        self.course = Course.objects.create(name="Software Engineering")
        self.other_course = Course.objects.create(name="Databases")
        self.material = Material.objects.create(
            title="Original title",
            description="Original description",
            uploaded_by=self.owner,
            course=self.course,
            university=self.university,
            file_type="summary",
            file=SimpleUploadedFile("orig.pdf", b"original content", content_type="application/pdf"),
        )
        self.url = reverse('materials:edit', kwargs={'pk': self.material.pk})

    def _payload(self, **overrides):
        data = {
            'title': 'New title',
            'description': 'New description',
            'course': self.other_course.pk,
            'university': self.other_university.pk,
            'file_type': 'exam',
        }
        data.update(overrides)
        return data

    def test_unauthenticated_user_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")
        self.material.file.delete(save=False)

    def test_owner_sees_prefilled_form_extending_base(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'materials/edit.html')
        self.assertTemplateUsed(response, 'base.html')
        form = response.context['form']
        self.assertEqual(form.initial['title'], "Original title")
        self.assertEqual(form.initial['description'], "Original description")
        self.assertEqual(form.initial['course'], self.course.pk)
        self.assertEqual(form.initial['university'], self.university.pk)
        self.assertEqual(form.initial['file_type'], "summary")
        self.material.file.delete(save=False)

    def test_non_owner_gets_403_on_get(self):
        self.client.login(email="other@eafit.edu.co", password="Password123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateNotUsed(response, 'materials/edit.html')
        self.material.file.delete(save=False)

    def test_non_owner_cannot_modify_via_post(self):
        self.client.login(email="other@eafit.edu.co", password="Password123!")
        response = self.client.post(self.url, self._payload())
        self.assertEqual(response.status_code, 403)
        self.material.refresh_from_db()
        self.assertEqual(self.material.title, "Original title")
        self.material.file.delete(save=False)

    def test_edit_nonexistent_material_returns_404(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        response = self.client.get(reverse('materials:edit', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)
        self.material.file.delete(save=False)

    def test_owner_updates_metadata_and_sees_success_message(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        old_name = self.material.file.name
        response = self.client.post(self.url, self._payload(), follow=True)
        self.assertRedirects(response, reverse('materials:detail', kwargs={'pk': self.material.pk}))
        self.assertContains(response, "Material updated successfully.")
        self.material.refresh_from_db()
        self.assertEqual(self.material.title, "New title")
        self.assertEqual(self.material.description, "New description")
        self.assertEqual(self.material.course, self.other_course)
        self.assertEqual(self.material.university, self.other_university)
        self.assertEqual(self.material.file_type, "exam")
        # Sin archivo nuevo, se conserva el actual
        self.assertEqual(self.material.file.name, old_name)
        self.material.file.delete(save=False)

    def test_owner_can_replace_file_and_old_file_is_removed(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        old_name = self.material.file.name
        storage = self.material.file.storage
        new_file = SimpleUploadedFile("new.pdf", b"new content", content_type="application/pdf")
        response = self.client.post(self.url, self._payload(file=new_file))
        self.assertEqual(response.status_code, 302)
        self.material.refresh_from_db()
        self.assertNotEqual(self.material.file.name, old_name)
        self.assertFalse(storage.exists(old_name))
        self.assertTrue(storage.exists(self.material.file.name))
        self.material.file.delete(save=False)

    def test_invalid_data_shows_errors_and_does_not_save(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        response = self.client.post(self.url, self._payload(title=''))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.material.refresh_from_db()
        self.assertEqual(self.material.title, "Original title")
        self.material.file.delete(save=False)

    def test_invalid_file_extension_is_rejected(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        bad = SimpleUploadedFile("script.exe", b"MZ", content_type="application/octet-stream")
        response = self.client.post(self.url, self._payload(file=bad))
        self.assertEqual(response.status_code, 200)
        self.assertIn('file', response.context['form'].errors)
        self.material.file.delete(save=False)

    def test_edit_button_only_visible_to_owner(self):
        detail_url = reverse('materials:detail', kwargs={'pk': self.material.pk})
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        self.assertContains(self.client.get(detail_url), self.url)
        self.client.logout()
        self.client.login(email="other@eafit.edu.co", password="Password123!")
        self.assertNotContains(self.client.get(detail_url), self.url)
        self.material.file.delete(save=False)

class MaterialDeleteTests(TestCase):
    """RF-25: eliminación de materiales por el uploader."""

    def setUp(self):
        self.university = University.objects.create(name="EAFIT")
        self.program = Program.objects.create(name="Ingeniería de Sistemas", university=self.university)
        self.owner = User.objects.create_user(
            email="owner@eafit.edu.co", password="Password123!",
            university=self.university, program=self.program,
        )
        self.other = User.objects.create_user(
            email="other@eafit.edu.co", password="Password123!",
            university=self.university, program=self.program,
        )
        self.course = Course.objects.create(name="Physics I")
        self.material = Material.objects.create(
            title="Delete me please",
            description="Outdated content",
            uploaded_by=self.owner,
            course=self.course,
            university=self.university,
            file_type="exam",
            file=SimpleUploadedFile("to_delete.pdf", b"content", content_type="application/pdf"),
        )
        self.url = reverse('materials:delete', kwargs={'pk': self.material.pk})
        self.detail_url = reverse('materials:detail', kwargs={'pk': self.material.pk})

    def test_unauthenticated_user_is_redirected_to_login(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")
        self.assertTrue(Material.objects.filter(pk=self.material.pk).exists())
        self.material.file.delete(save=False)

    def test_non_owner_gets_403_and_material_is_kept(self):
        self.client.login(email="other@eafit.edu.co", password="Password123!")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Material.objects.filter(pk=self.material.pk).exists())
        self.assertTrue(self.material.file.storage.exists(self.material.file.name))
        self.material.file.delete(save=False)

    def test_non_owner_gets_403_on_get(self):
        self.client.login(email="other@eafit.edu.co", password="Password123!")
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.material.file.delete(save=False)

    def test_get_by_owner_does_not_delete(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Material.objects.filter(pk=self.material.pk).exists())
        self.material.file.delete(save=False)

    def test_delete_nonexistent_material_returns_404(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        response = self.client.post(reverse('materials:delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)
        self.material.file.delete(save=False)

    def test_owner_deletes_record_and_physical_file(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        storage = self.material.file.storage
        file_name = self.material.file.name
        self.assertTrue(storage.exists(file_name))

        response = self.client.post(self.url)

        self.assertRedirects(response, reverse('materials:list'), fetch_redirect_response=False)
        self.assertFalse(Material.objects.filter(pk=self.material.pk).exists())
        self.assertFalse(storage.exists(file_name))

    def test_success_message_is_shown_after_deletion(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        response = self.client.post(self.url)
        texts = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("Study material deleted successfully.", texts)

    def test_deleted_material_no_longer_appears_in_search_or_filters(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        search_url = reverse('materials:search_materials')
        self.assertContains(self.client.get(search_url), "Delete me please")

        self.client.post(self.url)

        self.assertNotContains(self.client.get(search_url), "Delete me please")
        self.assertNotContains(self.client.get(search_url, {'q': 'Delete me'}), "Delete me please")
        self.assertNotContains(self.client.get(search_url, {'course': 'Physics I'}), "Delete me please")
        self.assertEqual(self.client.get(self.detail_url).status_code, 404)

    def test_ratings_and_downloads_are_removed_with_material(self):
        from materials.models import MaterialDownload, MaterialRating
        MaterialDownload.objects.create(material=self.material, user=self.other)
        MaterialRating.objects.create(material=self.material, user=self.other, score=5)
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        self.client.post(self.url)
        self.assertEqual(MaterialDownload.objects.count(), 0)
        self.assertEqual(MaterialRating.objects.count(), 0)

    def test_delete_button_and_modal_only_visible_to_owner(self):
        self.client.login(email="owner@eafit.edu.co", password="Password123!")
        response = self.client.get(self.detail_url)
        self.assertContains(response, 'id="delete-open"')
        self.assertContains(response, 'id="delete-dialog"')
        self.assertContains(response, "cannot be undone")
        self.client.logout()
        self.client.login(email="other@eafit.edu.co", password="Password123!")
        response = self.client.get(self.detail_url)
        self.assertNotContains(response, 'id="delete-open"')
        self.assertNotContains(response, 'id="delete-dialog"')
        self.material.file.delete(save=False)

class MaterialUniversityFilterTests(TestCase):
    """RF-26: filtro de materiales por universidad."""

    def setUp(self):
        self.eafit = University.objects.create(name="EAFIT")
        self.udea = University.objects.create(name="UdeA")
        self.program = Program.objects.create(name="Ingeniería de Sistemas", university=self.eafit)
        self.user = User.objects.create_user(
            email="user@eafit.edu.co", password="Password123!",
            university=self.eafit, program=self.program,
        )
        self.physics = Course.objects.create(name="Physics I")
        self.calculus = Course.objects.create(name="Calculus")
        self.client.login(email="user@eafit.edu.co", password="Password123!")
        self.search_url = reverse('materials:search_materials')

        self.m1 = self._make("Physics notes EAFIT", self.physics, self.eafit)
        self.m2 = self._make("Calculus notes EAFIT", self.calculus, self.eafit)
        self.m3 = self._make("Physics notes UdeA", self.physics, self.udea)

    def _make(self, title, course, university):
        return Material.objects.create(
            title=title, description="d", uploaded_by=self.user,
            course=course, university=university, file_type="notes",
            file=SimpleUploadedFile(f"{title}.pdf", b"x", content_type="application/pdf"),
        )

    def tearDown(self):
        for m in Material.objects.all():
            m.file.delete(save=False)

    def test_list_page_has_university_dropdown_and_extends_base(self):
        response = self.client.get(self.search_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'materials/list.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'id="university-select"')
        self.assertContains(response, 'All Universities')
        self.assertEqual(list(response.context['universities_list']), ["EAFIT", "UdeA"])

    def test_selecting_university_shows_only_its_materials(self):
        response = self.client.get(self.search_url, {'university': 'UdeA'})
        self.assertContains(response, "Physics notes UdeA")
        self.assertNotContains(response, "Physics notes EAFIT")
        self.assertNotContains(response, "Calculus notes EAFIT")
        self.assertEqual(response.context['selected_university'], 'UdeA')

    def test_clearing_filter_shows_all_materials_again(self):
        response = self.client.get(self.search_url, {'university': ''})
        for title in ("Physics notes EAFIT", "Calculus notes EAFIT", "Physics notes UdeA"):
            self.assertContains(response, title)
        self.assertEqual(self.client.get(self.search_url).context['materials'].count(), 3)

    def test_university_filter_combines_with_course_filter(self):
        response = self.client.get(self.search_url, {'university': 'EAFIT', 'course': 'Physics I'})
        self.assertContains(response, "Physics notes EAFIT")
        self.assertNotContains(response, "Calculus notes EAFIT")
        self.assertNotContains(response, "Physics notes UdeA")

    def test_university_filter_combines_with_keyword_search(self):
        response = self.client.get(self.search_url, {'university': 'EAFIT', 'q': 'Calculus'})
        self.assertContains(response, "Calculus notes EAFIT")
        self.assertNotContains(response, "Physics notes EAFIT")
        self.assertNotContains(response, "Physics notes UdeA")

    def test_university_filter_is_case_insensitive(self):
        response = self.client.get(self.search_url, {'university': 'udea'})
        self.assertContains(response, "Physics notes UdeA")
        self.assertNotContains(response, "Physics notes EAFIT")

    def test_unknown_university_shows_empty_state(self):
        response = self.client.get(self.search_url, {'university': 'Nowhere'})
        self.assertEqual(response.context['materials'].count(), 0)
        self.assertContains(response, 'No study materials found for university "Nowhere"')

    def test_selected_university_is_preselected_in_dropdown(self):
        response = self.client.get(self.search_url, {'university': 'UdeA'})
        self.assertContains(response, 'value="UdeA" selected')

    def test_university_filter_is_kept_when_sorting(self):
        response = self.client.get(self.search_url, {'university': 'EAFIT', 'sort': 'rating'})
        self.assertEqual(response.context['materials'].count(), 2)
        self.assertEqual(response.context['sort_by'], 'rating')

    def test_university_filter_requires_login(self):
        self.client.logout()
        response = self.client.get(self.search_url, {'university': 'EAFIT'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)