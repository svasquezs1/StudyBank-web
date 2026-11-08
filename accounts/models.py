from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import EmailValidator, FileExtensionValidator, RegexValidator
from django.db import models


class University(models.Model):
    name = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.name


class Program(models.Model):
    name = models.CharField(max_length=150)
    university = models.ForeignKey(
        University, on_delete=models.CASCADE, related_name='programs'
    )

    def __str__(self):
        return f"{self.name} ({self.university.name})"


institutional_email_validator = RegexValidator(
    regex=r'^[\w.+-]+@eafit\.edu\.co$',
    message='You must use an institutional email (@eafit.edu.co).',
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(
        unique=True,
        validators=[EmailValidator(), institutional_email_validator],
    )
    university = models.ForeignKey(
        University, on_delete=models.SET_NULL, null=True, blank=True
    )
    program = models.ForeignKey(
        Program, on_delete=models.SET_NULL, null=True, blank=True
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
        ],
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        """
        RF-23: name shown on public pages. Uses the full name when the user
        filled it in; otherwise the part of the email before "@", so the
        complete institutional email is not exposed on the public profile.
        """
        return self.get_full_name() or self.email.split('@')[0]
    