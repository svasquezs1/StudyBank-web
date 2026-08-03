from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import TutorRegistrationForm
from .models import TutorProfile


@login_required
def register_tutor(request):
    if hasattr(request.user, "tutor_profile"):
        return redirect("home")

    if request.method == "POST":
        form = TutorRegistrationForm(request.POST)

        if form.is_valid():
            tutor_profile = form.save(commit=False)
            tutor_profile.user = request.user
            tutor_profile.save()
            form.save_m2m()

            return redirect("home")
    else:
        form = TutorRegistrationForm()

    return render(
        request,
        "tutoring/register_tutor.html",
        {"form": form},
    )