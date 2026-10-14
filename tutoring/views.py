from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import (
    TutorAvailabilityForm,
    TutorRegistrationForm,
    TutoringRatingForm,
    TutoringRequestForm,
)
from .models import (
    Subject,
    TutorAvailability,
    TutoringRating,
    TutoringRequest,
    TutorProfile,
)


@login_required
def register_tutor(request):
    if hasattr(request.user, "tutor_profile"):
        return redirect("home")

    if request.method == "POST":
        form = TutorRegistrationForm(
            request.POST
        )

        if form.is_valid():
            tutor_profile = form.save(
                commit=False
            )
            tutor_profile.user = request.user
            tutor_profile.save()
            form.save_m2m()

            return redirect("home")
    else:
        form = TutorRegistrationForm()

    return render(
        request,
        "tutoring/register_tutor.html",
        {
            "form": form,
        },
    )


@login_required
def tutor_search(request):
    subjects = Subject.objects.all().order_by(
        "name"
    )

    selected_subject = request.GET.get(
        "subject",
        "",
    )

    search_query = request.GET.get(
        "q",
        "",
    ).strip()

    selected_sort = request.GET.get(
        "sort",
        "alphabetical",
    )

    valid_sort_options = {
        "alphabetical",
        "rating",
        "popular",
    }

    if selected_sort not in valid_sort_options:
        selected_sort = "alphabetical"

    tutors = (
        TutorProfile.objects
        .filter(
            is_approved=True
        )
        .select_related(
            "user"
        )
    )

    if selected_subject:
        tutors = tutors.filter(
            subjects__id=selected_subject
        )

    if search_query:
        tutors = tutors.filter(
            user__email__icontains=search_query
        )

    tutors = tutors.annotate(
        average_rating_value=Avg(
            "ratings__score"
        ),
        rating_count=Count(
            "ratings",
            distinct=True,
        ),
    )

    if selected_sort == "rating":
        tutors = tutors.order_by(
            F(
                "average_rating_value"
            ).desc(
                nulls_last=True
            ),
            F(
                "rating_count"
            ).desc(),
            "user__email",
        )

    elif selected_sort == "popular":
        tutors = tutors.order_by(
            F(
                "rating_count"
            ).desc(),
            F(
                "average_rating_value"
            ).desc(
                nulls_last=True
            ),
            "user__email",
        )

    else:
        tutors = tutors.order_by(
            "user__email"
        )

    tutors = tutors.prefetch_related(
        "subjects"
    )

    return render(
        request,
        "tutoring/tutor_search.html",
        {
            "subjects": subjects,
            "selected_subject": selected_subject,
            "search_query": search_query,
            "selected_sort": selected_sort,
            "tutors": tutors,
        },
    )


@login_required
def tutor_availability(request):
    tutor = get_object_or_404(
        TutorProfile,
        user=request.user,
        is_approved=True,
    )

    availability_slots = (
        TutorAvailability.objects.filter(
            tutor=tutor
        )
    )

    if request.method == "POST":
        form = TutorAvailabilityForm(
            request.POST,
            tutor=tutor,
        )

        if form.is_valid():
            availability = form.save(
                commit=False
            )

            availability.tutor = tutor
            availability.save()

            return redirect(
                "tutoring:availability"
            )

    else:
        form = TutorAvailabilityForm(
            tutor=tutor
        )

    return render(
        request,
        "tutoring/availability.html",
        {
            "form": form,
            "availability_slots": availability_slots,
        },
    )


@login_required
def edit_availability(
    request,
    availability_id,
):
    tutor = get_object_or_404(
        TutorProfile,
        user=request.user,
        is_approved=True,
    )

    availability = get_object_or_404(
        TutorAvailability,
        id=availability_id,
        tutor=tutor,
    )

    if request.method == "POST":
        form = TutorAvailabilityForm(
            request.POST,
            instance=availability,
            tutor=tutor,
        )

        if form.is_valid():
            form.save()

            return redirect(
                "tutoring:availability"
            )

    else:
        form = TutorAvailabilityForm(
            instance=availability,
            tutor=tutor,
        )

    return render(
        request,
        "tutoring/edit_availability.html",
        {
            "form": form,
            "availability": availability,
        },
    )


@login_required
@require_POST
def delete_availability(
    request,
    availability_id,
):
    tutor = get_object_or_404(
        TutorProfile,
        user=request.user,
        is_approved=True,
    )

    availability = get_object_or_404(
        TutorAvailability,
        id=availability_id,
        tutor=tutor,
    )

    availability.delete()

    return redirect(
        "tutoring:availability"
    )


@login_required
def request_tutoring(
    request,
    tutor_id,
):
    tutor = get_object_or_404(
        TutorProfile.objects
        .select_related("user")
        .prefetch_related("subjects"),
        id=tutor_id,
        is_approved=True,
    )

    if tutor.user_id == request.user.id:
        return redirect(
            "tutoring:tutor_search"
        )

    if request.method == "POST":
        form = TutoringRequestForm(
            request.POST,
            tutor=tutor,
        )

        if form.is_valid():
            tutoring_request = form.save(
                commit=False
            )

            tutoring_request.student = (
                request.user
            )

            tutoring_request.tutor = tutor
            tutoring_request.save()

            return redirect(
                f"{reverse('tutoring:my_requests')}"
                "?sent=1"
            )

    else:
        form = TutoringRequestForm(
            tutor=tutor
        )

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
        .filter(
            student=request.user
        )
        .select_related(
            "tutor__user",
            "subject",
        )
    )

    request_sent = (
        request.GET.get("sent") == "1"
    )

    rating_saved = (
        request.GET.get("rated") == "1"
    )

    return render(
        request,
        "tutoring/my_requests.html",
        {
            "tutoring_requests": tutoring_requests,
            "request_sent": request_sent,
            "rating_saved": rating_saved,
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
        .filter(
            tutor=tutor
        )
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
def accept_tutoring_request(
    request,
    request_id,
):
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

    if (
        tutoring_request.status
        == TutoringRequest.Status.PENDING
    ):
        tutoring_request.status = (
            TutoringRequest.Status.ACCEPTED
        )

        tutoring_request.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    return redirect(
        "tutoring:incoming_requests"
    )


@login_required
@require_POST
def reject_tutoring_request(
    request,
    request_id,
):
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

    if (
        tutoring_request.status
        == TutoringRequest.Status.PENDING
    ):
        tutoring_request.status = (
            TutoringRequest.Status.REJECTED
        )

        tutoring_request.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    return redirect(
        "tutoring:incoming_requests"
    )


@login_required
@require_POST
def complete_tutoring_request(
    request,
    request_id,
):
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

    if (
        tutoring_request.status
        == TutoringRequest.Status.ACCEPTED
    ):
        tutoring_request.status = (
            TutoringRequest.Status.COMPLETED
        )

        tutoring_request.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

    return redirect(
        "tutoring:incoming_requests"
    )


@login_required
def rate_tutoring_request(
    request,
    request_id,
):
    tutoring_request = get_object_or_404(
        TutoringRequest.objects.select_related(
            "tutor__user",
            "subject",
        ),
        id=request_id,
        student=request.user,
        status=TutoringRequest.Status.COMPLETED,
    )

    existing_rating = (
        TutoringRating.objects
        .filter(
            tutoring_request=tutoring_request
        )
        .first()
    )

    if existing_rating is not None:
        return render(
            request,
            "tutoring/rate_session.html",
            {
                "tutoring_request": tutoring_request,
                "existing_rating": existing_rating,
                "form": None,
            },
        )

    if request.method == "POST":
        form = TutoringRatingForm(
            request.POST
        )

        if form.is_valid():
            rating = form.save(
                commit=False
            )

            rating.tutoring_request = (
                tutoring_request
            )

            rating.student = request.user
            rating.tutor = (
                tutoring_request.tutor
            )

            rating.save()

            return redirect(
                f"{reverse('tutoring:my_requests')}"
                "?rated=1"
            )

    else:
        form = TutoringRatingForm()

    return render(
        request,
        "tutoring/rate_session.html",
        {
            "tutoring_request": tutoring_request,
            "existing_rating": None,
            "form": form,
        },
    )
