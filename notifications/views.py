from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Notification


@login_required
def notification_list(request):
    notifications = list(
        Notification.objects
        .filter(recipient=request.user)
        .select_related("tutoring_request")[:50]
    )

    # Opening the page marks the user's notifications as read.
    Notification.objects.filter(
        recipient=request.user,
        is_read=False,
    ).update(is_read=True)

    return render(
        request,
        "notifications/notification_list.html",
        {"notifications": notifications},
    )
