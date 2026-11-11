from django.urls import path

from . import views
from .auth_views import StudyBankLoginView, StudyBankLogoutView

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', StudyBankLoginView.as_view(), name='login'),
    path('logout/', StudyBankLogoutView.as_view(), name='logout'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('users/<int:user_id>/', views.public_profile, name='public_profile'),
]
