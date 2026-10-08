import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count

from accounts.models import University

MAX_UPLOAD_SIZE_MB = 20
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_EXTENSIONS = ['pdf', 'docx', 'png', 'jpg', 'jpeg']

def validate_file_size(file):
    if file.size > MAX_UPLOAD_SIZE_BYTES:
        raise ValidationError(f'File size cannot exceed {MAX_UPLOAD_SIZE_MB} MB.')

class Course(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name

class Material(models.Model):
    class FileType(models.TextChoices):
        EXAM = 'exam', 'Exam'
        SUMMARY = 'summary', 'Summary'
        NOTES = 'notes', 'Notes'
        LAB_REPORT = 'lab_report', 'Lab Report'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='materials'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='materials')
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='materials')
    file_type = models.CharField(max_length=20, choices=FileType.choices)
    file = models.FileField(
        upload_to='materials/',
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS),
            validate_file_size,
        ],
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title

    @property
    def file_extension(self):
        """Devuelve la extensión del archivo en mayúsculas (ej. PDF, DOCX)"""
        if self.file and hasattr(self.file, 'name'):
            ext = os.path.splitext(self.file.name)[1]
            return ext.replace('.', '').upper()
        return ''

    # ----- RF-13: calificación de materiales -----

    def rating_summary(self):
        """Promedio y total de calificaciones en una sola consulta agregada."""
        aggregate = self.ratings.aggregate(average=Avg('score'), total=Count('id'))
        return {
            'average': round(aggregate['average'], 1) if aggregate['average'] is not None else 0,
            'count': aggregate['total'] or 0,
        }

    @property
    def average_rating(self):
        return self.rating_summary()['average']

    @property
    def rating_count(self):
        return self.rating_summary()['count']

    def downloaded_by(self, user):
        """Indica si un usuario autenticado ya descargó este material (RF-13)."""
        if not user or not user.is_authenticated:
            return False
        return self.downloads.filter(user=user).exists()

    def rating_by(self, user):
        """Devuelve la calificación existente del usuario, o None."""
        if not user or not user.is_authenticated:
            return None
        return self.ratings.filter(user=user).first()

class MaterialDownload(models.Model):
    """Registra que un usuario descargó un material. Habilita la calificación (RF-13)."""
    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, related_name='downloads'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='material_downloads'
    )
    first_downloaded_at = models.DateTimeField(auto_now_add=True)
    last_downloaded_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['material', 'user'], name='unique_material_download_per_user'
            )
        ]

    def __str__(self):
        return f'{self.user} downloaded {self.material}'

class MaterialRating(models.Model):
    """Calificación de 1 a 5 estrellas, única por usuario y material (RF-13)."""
    MIN_SCORE = 1
    MAX_SCORE = 5

    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, related_name='ratings'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='material_ratings'
    )
    score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_SCORE), MaxValueValidator(MAX_SCORE)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['material', 'user'], name='unique_material_rating_per_user'
            )
        ]

    def __str__(self):
        return f'{self.user} rated {self.material} with {self.score} stars'

