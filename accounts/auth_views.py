"""
Login and logout views with feedback messages (RF-02, RF-21).

The error message is the same for every failed login (wrong email, wrong
password, unregistered or inactive account, empty fields), so the page never
reveals whether an email is registered or which field was wrong.
"""
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView

LOGIN_ERROR_MESSAGE = (
    "We couldn't log you in. Check your email and password and try again."
)
LOGIN_SUCCESS_MESSAGE = 'Welcome back, {name}!'
LOGOUT_SUCCESS_MESSAGE = 'You have logged out successfully.'


class StudyBankLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.get_user()
        name = user.get_short_name() or user.email.split('@')[0]
        messages.success(self.request, LOGIN_SUCCESS_MESSAGE.format(name=name))
        return response

    def form_invalid(self, form):
        messages.error(self.request, LOGIN_ERROR_MESSAGE)
        return super().form_invalid(form)


class StudyBankLogoutView(LogoutView):
    next_page = 'home'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, LOGOUT_SUCCESS_MESSAGE)
        return response
    