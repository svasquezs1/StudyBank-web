from django.contrib import admin

from .models import Subject, TutorProfile


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