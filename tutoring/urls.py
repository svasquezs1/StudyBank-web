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
        "requests/",
        views.my_tutoring_requests,
        name="my_requests",
    ),
    path(
        "requests/incoming/",
        views.incoming_tutoring_requests,
        name="incoming_requests",
    ),
    path(
        "requests/<int:request_id>/accept/",
        views.accept_tutoring_request,
        name="accept_request",
    ),
    path(
        "requests/<int:request_id>/reject/",
        views.reject_tutoring_request,
        name="reject_request",
    ),
]
