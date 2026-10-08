from django.contrib import admin

from .models import Course, Material, MaterialDownload, MaterialRating


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_by', 'course', 'university', 'file_type', 'uploaded_at')
    list_filter = ('file_type', 'university', 'course')
    search_fields = ('title', 'uploaded_by__email')


@admin.register(MaterialDownload)
class MaterialDownloadAdmin(admin.ModelAdmin):
    list_display = ('material', 'user', 'first_downloaded_at', 'last_downloaded_at')
    search_fields = ('material__title', 'user__email')


@admin.register(MaterialRating)
class MaterialRatingAdmin(admin.ModelAdmin):
    list_display = ('material', 'user', 'score', 'updated_at')
    list_filter = ('score',)
    search_fields = ('material__title', 'user__email')
