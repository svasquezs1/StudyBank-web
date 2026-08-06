from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, University, Program
from materials.models import Material, Course


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