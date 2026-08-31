from django.urls import path

from . import views

app_name = "tutoring"

urlpatterns = [
    path(
        "register/",
        views.register_tutor,
        name="register_tutor",
    ),
    path(
        "search/",
        views.tutor_search,
        name="tutor_search",
    ),
    path(
        "request/<int:tutor_id>/",
        views.request_tutoring,
        name="request_tutoring",
    ),
    path(
        "requests/<int:request_id>/confirmation/",
        views.tutoring_request_confirmation,
        name="tutoring_request_confirmation",
    ),
]
