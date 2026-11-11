from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProfileEditForm, RegisterForm
from .models import User

# RF-23: number of shared materials listed on the public profile.
PUBLIC_PROFILE_MATERIALS_LIMIT = 6


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


@login_required
def public_profile(request, user_id):
    """
    RF-23: public profile of a registered user.

    Only the fields defined as public are sent to the template: display name,
    profile picture, university, program, member-since date, approved tutor
    status and the materials the user shared. The email, login data and
    permissions are never shown. Inactive accounts return 404.
    """
    profile_user = get_object_or_404(
        User.objects.select_related('university', 'program'),
        pk=user_id,
        is_active=True,
    )

    shared_materials = profile_user.materials.select_related('course')
    tutor_profile = getattr(profile_user, 'tutor_profile', None)

    context = {
        'profile_user': profile_user,
        'shared_materials': shared_materials[:PUBLIC_PROFILE_MATERIALS_LIMIT],
        'shared_materials_total': shared_materials.count(),
        'approved_tutor': tutor_profile if tutor_profile and tutor_profile.is_approved else None,
        'is_own_profile': profile_user.pk == request.user.pk,
    }
    return render(request, 'accounts/public_profile.html', context)
