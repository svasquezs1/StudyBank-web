from django.contrib import admin

from .models import Course, Material


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_by', 'course', 'university', 'file_type', 'uploaded_at')
    list_filter = ('file_type', 'university', 'course')
    search_fields = ('title', 'uploaded_by__email')
