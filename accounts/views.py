from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ProfileEditForm, RegisterForm


REGISTER_SUCCESS_MESSAGE = 'Your account was created successfully. Welcome to StudyBank!'
REGISTER_ERROR_MESSAGE = (
    "We couldn't create your account with the information provided. "
    'Check the requirements below and try again.'
)


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, REGISTER_SUCCESS_MESSAGE)
            return redirect('home')
        # Same message for every error (email already registered, invalid
        # email, weak or mismatched passwords, missing fields), so the page
        # never reveals which value failed or whether an email has an account.
        messages.error(request, REGISTER_ERROR_MESSAGE)
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:edit_profile')
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, 'accounts/edit_profile.html', {'form': form})
