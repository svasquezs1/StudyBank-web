"""
Access control for uploaded files (study materials and profile pictures).

Django serves the files of MEDIA_ROOT under /media/ when they are stored on the
server disk (local development and the AWS EC2 instance). Only logged-in users
can open them: an anonymous visitor who opens a /media/ URL is sent to the
login page, as with any other private page of StudyBank.
"""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.static import serve


@login_required
def protected_media(request, path):
    # serve() rejects paths outside MEDIA_ROOT and answers 404 for missing files.
    response = serve(request, path, document_root=settings.MEDIA_ROOT)
    # The file belongs to a logged-in session: browsers may cache it, but
    # shared caches and proxies must not.
    response['Cache-Control'] = 'private, max-age=3600'
    return response
