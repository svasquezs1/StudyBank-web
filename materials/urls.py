from django.urls import path

from . import views

app_name = 'materials'

urlpatterns = [
    path('upload/', views.upload, name='upload'),
    path('', views.material_list, name='list'),
    # RF-06, RF-07, RF-08 views will be added here
]