# progress/admin.py
from django.contrib import admin

from .models import LessonProgress, LevelProgress

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    """
    Admin ya kufuatilia completion ya masomo (snapshot progress).
    """
    list_display = (
        "user",
        "lesson",
        "status",
        "score",
        "completed_at",
    )
    list_filter = (
        "status",
        "lesson__level",
        "lesson__level__path",
    )
    search_fields = (
        "user__username",
        "user__email",
        "lesson__title",
        "lesson__level__name",
        "lesson__level__path__name",
    )
    autocomplete_fields = ("user", "lesson")
    readonly_fields = ("completed_at",)
    date_hierarchy = "completed_at"
    ordering = ("-completed_at",)


@admin.register(LevelProgress)
class LevelProgressAdmin(admin.ModelAdmin):
    """
    Admin ya kufuatilia completion ya levels (Seeker / Scholar / Missionary).
    """
    list_display = (
        "user",
        "level",
        "status",
        "completed_at",
    )
    list_filter = (
        "status",
        "level__path",
    )
    search_fields = (
        "user__username",
        "user__email",
        "level__name",
        "level__path__name",
    )
    autocomplete_fields = ("user", "level")
    readonly_fields = ("completed_at",)
    date_hierarchy = "completed_at"
    ordering = ("-completed_at",)
