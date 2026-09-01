from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import TutorRegistrationForm, TutoringRequestForm
from .models import Subject, TutoringRequest, TutorProfile


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


@login_required
def request_tutoring(request, tutor_id):
    tutor = get_object_or_404(
        TutorProfile.objects.select_related("user").prefetch_related("subjects"),
        id=tutor_id,
        is_approved=True,
    )

    if tutor.user_id == request.user.id:
        return redirect("tutoring:tutor_search")

    if request.method == "POST":
        form = TutoringRequestForm(
            request.POST,
            tutor=tutor,
        )

        if form.is_valid():
            tutoring_request = form.save(commit=False)
            tutoring_request.student = request.user
            tutoring_request.tutor = tutor
            tutoring_request.save()

            return redirect(
                f"{reverse('tutoring:my_requests')}?sent=1"
            )
    else:
        form = TutoringRequestForm(tutor=tutor)

    return render(
        request,
        "tutoring/request_tutoring.html",
        {
            "form": form,
            "tutor": tutor,
        },
    )


@login_required
def my_tutoring_requests(request):
    tutoring_requests = (
        TutoringRequest.objects
        .filter(student=request.user)
        .select_related(
            "tutor__user",
            "subject",
        )
    )

    request_sent = request.GET.get("sent") == "1"

    return render(
        request,
        "tutoring/my_requests.html",
        {
            "tutoring_requests": tutoring_requests,
            "request_sent": request_sent,
        },
    )


@login_required
def incoming_tutoring_requests(request):
    tutor = get_object_or_404(
        TutorProfile,
        user=request.user,
        is_approved=True,
    )

    tutoring_requests = (
        TutoringRequest.objects
        .filter(tutor=tutor)
        .select_related(
            "student",
            "subject",
        )
    )

    return render(
        request,
        "tutoring/incoming_requests.html",
        {
            "tutoring_requests": tutoring_requests,
        },
    )


@login_required
@require_POST
def accept_tutoring_request(request, request_id):
    tutor = get_object_or_404(
        TutorProfile,
        user=request.user,
        is_approved=True,
    )

    tutoring_request = get_object_or_404(
        TutoringRequest,
        id=request_id,
        tutor=tutor,
    )

    if tutoring_request.status == TutoringRequest.Status.PENDING:
        tutoring_request.status = TutoringRequest.Status.ACCEPTED
        tutoring_request.save(update_fields=["status", "updated_at"])

    return redirect("tutoring:incoming_requests")


@login_required
@require_POST
def reject_tutoring_request(request, request_id):
    tutor = get_object_or_404(
        TutorProfile,
        user=request.user,
        is_approved=True,
    )

    tutoring_request = get_object_or_404(
        TutoringRequest,
        id=request_id,
        tutor=tutor,
    )

    if tutoring_request.status == TutoringRequest.Status.PENDING:
        tutoring_request.status = TutoringRequest.Status.REJECTED
        tutoring_request.save(update_fields=["status", "updated_at"])

    return redirect("tutoring:incoming_requests")
