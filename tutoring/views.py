from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import TutorRegistrationForm
from .models import Subject, TutorProfile


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


@login_required
def tutor_search(request):
    subjects = Subject.objects.all().order_by("name")
    selected_subject = request.GET.get("subject")

    tutors = TutorProfile.objects.filter(
        is_approved=True
    ).select_related("user")

    if selected_subject:
        tutors = tutors.filter(subjects__id=selected_subject)

    tutors = tutors.prefetch_related("subjects").distinct()

    return render(
        request,
        "tutoring/tutor_search.html",
        {
            "subjects": subjects,
            "selected_subject": selected_subject,
            "tutors": tutors,
        },
    )