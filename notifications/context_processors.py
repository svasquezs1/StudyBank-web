def unread_notifications(request):
    """Makes the unread notifications count available in every template."""
    if not request.user.is_authenticated:
        return {}

    return {
        "unread_notifications_count": request.user.notifications.filter(
            is_read=False
        ).count()
    }
