import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

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