from django.urls import path

from . import views

app_name = 'materials'

urlpatterns = [
    path('upload/', views.upload, name='upload'),
    path('', views.material_list, name='list'),
    path('<int:pk>/', views.material_detail, name='detail'),
]