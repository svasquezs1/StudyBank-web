from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "notifications"

    def ready(self):
        # Registers the signal receivers that create notifications.
        from . import signals  # noqa: F401
