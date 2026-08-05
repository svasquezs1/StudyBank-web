from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, University, Program
from materials.models import Material, Course


class MaterialDetailViewTests(TestCase):
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
        fake_file = SimpleUploadedFile("test_doc.pdf", b"file content", content_type="application/pdf")
        
        self.material = Material.objects.create(
            title="Partial Exam Summary",
            description="Detailed review notes for first exam",
            uploaded_by=self.user,
            course=self.course,
            university=self.university,
            file_type="summary",
            file=fake_file
        )

    def test_unauthenticated_user_redirected_to_login(self):
        """Criterio 1: Usuarios no autenticados son redirigidos a /login/"""
        url = reverse('materials:detail', kwargs={'pk': self.material.pk})
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_authenticated_user_can_view_material_details(self):
        """Criterios 1, 2, 3 y 5: Usuario autenticado ve todos los datos y usa el template base"""
        self.client.login(email="testuser@eafit.edu.co", password="Password123!")
        url = reverse('materials:detail', kwargs={'pk': self.material.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'materials/detail.html')
        self.assertContains(response, self.material.title)
        self.assertContains(response, self.material.description)
        self.assertContains(response, self.material.course.name)
        self.assertContains(response, self.material.university.name)
        self.assertContains(response, self.material.file.url)

    def test_invalid_material_id_returns_404(self):
        """Criterio 4: ID que no existe devuelve error 404"""
        self.client.login(email="testuser@eafit.edu.co", password="Password123!")
        url = reverse('materials:detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)