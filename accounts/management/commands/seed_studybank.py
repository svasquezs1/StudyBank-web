"""
Loads the shared starting data of StudyBank, so every team member (and the
AWS EC2 instance) works with the same catalogs and administrator accounts.

Usage:
    python manage.py seed_studybank
    python manage.py seed_studybank --reset-admin-passwords

What it creates:
    - The university, programs, courses and tutoring subjects listed below.
    - One administrator account (staff and superuser) per team member.

The administrators' password is read from SEED_ADMIN_PASSWORD in the .env
file, which is never committed: the repository is public, so the password
must not be written in the code.

The command can be run any number of times: existing records are kept and
nothing is duplicated. Existing passwords are only changed with
--reset-admin-passwords.
"""
import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Program, University, User
from materials.models import Course
from tutoring.models import Subject

UNIVERSITY = 'Universidad EAFIT'

PROGRAMS = [
    'Systems Engineering',
    'Mathematical Engineering',
    'Production Engineering',
    'Mechanical Engineering',
    'Civil Engineering',
    'Business Administration',
]

# Courses for study materials (materials app).
COURSES = [
    'Calculus I',
    'Calculus II',
    'Calculus III',
    'Linear Algebra',
    'Physics I',
    'Discrete Mathematics',
    'Probability and Statistics',
    'Programming Fundamentals',
    'Data Structures and Algorithms',
    'Databases',
    'Operating Systems',
    'Software Engineering',
]

# Subjects that tutors can teach (tutoring app).
SUBJECTS = list(COURSES)

ADMINS = [
    {'email': 'sebastian@eafit.edu.co', 'first_name': 'Sebastián', 'last_name': 'Vásquez'},
    {'email': 'gisel@eafit.edu.co', 'first_name': 'Gisel', 'last_name': 'Jaramillo'},
    {'email': 'samuel@eafit.edu.co', 'first_name': 'Samuel', 'last_name': 'Serna'},
]
ADMIN_PROGRAM = 'Systems Engineering'

PASSWORD_ENV_VAR = 'SEED_ADMIN_PASSWORD'


class Command(BaseCommand):
    help = 'Loads the shared catalogs and the team administrator accounts.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-admin-passwords',
            action='store_true',
            help=f'Set the password of existing administrators to {PASSWORD_ENV_VAR}.',
        )

    def handle(self, *args, **options):
        password = os.environ.get(PASSWORD_ENV_VAR, '')
        if not password:
            raise CommandError(
                f'{PASSWORD_ENV_VAR} is not set. Add it to your .env file '
                '(the team shares the value privately) and run the command again.'
            )
        try:
            validate_password(password)
        except ValidationError as error:
            raise CommandError(
                f'{PASSWORD_ENV_VAR} is too weak: ' + ' '.join(error.messages)
            ) from error

        with transaction.atomic():
            university, created = University.objects.get_or_create(name=UNIVERSITY)
            self.report('University', 1 if created else 0, 1)

            programs = {}
            new = 0
            for name in PROGRAMS:
                programs[name], created = Program.objects.get_or_create(
                    name=name, university=university
                )
                new += created
            self.report('Programs', new, len(PROGRAMS))

            new = 0
            for name in COURSES:
                # Course.name is not unique in the database: reuse the first match.
                if not Course.objects.filter(name=name).exists():
                    Course.objects.create(name=name)
                    new += 1
            self.report('Courses', new, len(COURSES))

            new = 0
            for name in SUBJECTS:
                new += Subject.objects.get_or_create(name=name)[1]
            self.report('Tutoring subjects', new, len(SUBJECTS))

            for data in ADMINS:
                self.seed_admin(
                    data, password, university, programs[ADMIN_PROGRAM],
                    options['reset_admin_passwords'],
                )

        self.stdout.write(self.style.SUCCESS('StudyBank data is ready.'))

    def seed_admin(self, data, password, university, program, reset_password):
        user = User.objects.filter(email=data['email']).first()
        if user is None:
            user = User(email=data['email'])
            user.set_password(password)
            status = 'created'
        elif reset_password:
            user.set_password(password)
            status = 'password reset'
        else:
            status = 'already exists (password unchanged)'

        user.first_name = user.first_name or data['first_name']
        user.last_name = user.last_name or data['last_name']
        user.university = user.university or university
        user.program = user.program or program
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.stdout.write(f'  Administrator {user.email}: {status}')

    def report(self, label, new, total):
        self.stdout.write(f'  {label}: {new} new, {total - new} already existed')
