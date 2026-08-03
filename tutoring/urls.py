from django.urls import path

from . import views

app_name = "tutoring"

urlpatterns = [
    path("register/", views.register_tutor, name="register_tutor"),
    path("search/", views.tutor_search, name="tutor_search"),
]