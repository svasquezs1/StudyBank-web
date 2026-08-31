from django.contrib import admin

from .models import Subject, TutoringRequest, TutorProfile


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "is_approved")
    list_filter = ("is_approved",)
    search_fields = ("user__email",)
    filter_horizontal = ("subjects",)


@admin.register(TutoringRequest)
class TutoringRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "tutor",
        "subject",
        "scheduled_at",
        "mode",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "mode",
        "subject",
    )

    search_fields = (
        "student__email",
        "tutor__user__email",
        "subject__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )
