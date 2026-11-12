"""
URL configuration for config project.
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path

from . import views
from .media import protected_media

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('materials/', include('materials.urls')),
    path('tutoring/', include('tutoring.urls')),
    path('notifications/', include('notifications.urls')),
]

if getattr(settings, 'MEDIA_ROOT', None) and (settings.DEBUG or settings.SERVE_MEDIA):
    # Uploaded files stored on the server disk (local development and AWS EC2)
    # are served by Django only to logged-in users.
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', protected_media, name='protected_media'),
    ]
