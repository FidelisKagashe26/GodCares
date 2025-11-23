# discipleship/admin.py
from django.contrib import admin

from .models import (
    DiscipleshipPath,
    DiscipleshipLevel,
    DiscipleshipLesson,
    LessonProgress,
    PathEnrollment,
    Quiz,
    QuizQuestion,
    QuizChoice,
    QuizAttempt,
)


# ====== Inlines ======


class DiscipleshipLevelInline(admin.TabularInline):
    """
    Ku-edit levels moja kwa moja ndani ya Path.
    """
    model = DiscipleshipLevel
    extra = 1
    fields = ("name", "order", "is_active")
    show_change_link = True


class DiscipleshipLessonInline(admin.TabularInline):
    """
    Ku-edit lessons ndani ya Level.
    """
    model = DiscipleshipLesson
    extra = 1
    fields = ("title", "order", "is_published", "points_value")
    show_change_link = True


class QuizChoiceInline(admin.TabularInline):
    """
    Kuongeza choices za swali moja kwa moja kwenye QuizQuestion.
    """
    model = QuizChoice
    extra = 2
    fields = ("choice_text", "is_correct", "order")


class QuizQuestionInline(admin.TabularInline):
    """
    Kuongeza maswali ya Quiz ndani ya Quiz admin.
    """
    model = QuizQuestion
    extra = 1
    show_change_link = True
    fields = ("question_type", "question_text", "points", "order")


# ====== Main Models ======


@admin.register(DiscipleshipPath)
class DiscipleshipPathAdmin(admin.ModelAdmin):
    list_display = ("name", "stage", "order", "is_active", "created_at")
    list_filter = ("stage", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("order",)
    inlines = [DiscipleshipLevelInline]


@admin.register(DiscipleshipLevel)
class DiscipleshipLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "path", "order", "required_score", "is_active", "created_at")
    list_filter = ("path", "is_active")
    search_fields = ("name", "description", "path__name")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("path", "order")
    inlines = [DiscipleshipLessonInline]
    autocomplete_fields = ("path",)


@admin.register(DiscipleshipLesson)
class DiscipleshipLessonAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "level",
        "order",
        "is_published",
        "points_value",
        "duration_minutes",
        "created_at",
    )
    list_filter = ("is_published", "level", "level__path")
    search_fields = (
        "title",
        "description",
        "bible_references",
        "level__name",
        "level__path__name",
    )
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("level__path", "level__order", "order")
    autocomplete_fields = ("level",)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "status", "score", "completed_at", "created_at")
    list_filter = ("status", "lesson__level__path", "lesson__level")
    search_fields = (
        "user__username",
        "user__email",
        "lesson__title",
        "lesson__level__name",
        "lesson__level__path__name",
    )
    autocomplete_fields = ("user", "lesson")
    readonly_fields = ("created_at", "last_accessed", "started_at", "completed_at")


@admin.register(PathEnrollment)
class PathEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "path",
        "current_level",
        "progress_percentage",
        "is_active",
        "enrolled_at",
        "completed_at",
    )
    list_filter = ("is_active", "path")
    search_fields = (
        "user__username",
        "user__email",
        "path__name",
        "current_level__name",
    )
    autocomplete_fields = ("user", "path", "current_level")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("lesson", "title", "passing_score", "time_limit_minutes", "max_attempts", "is_active")
    list_filter = ("is_active", "lesson__level__path")
    search_fields = ("title", "lesson__title", "lesson__level__name", "lesson__level__path__name")
    inlines = [QuizQuestionInline]
    autocomplete_fields = ("lesson",)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "question_type", "question_text", "points", "order")
    list_filter = ("question_type", "quiz__lesson__level__path")
    search_fields = ("question_text", "quiz__title", "quiz__lesson__title")
    ordering = ("quiz", "order")
    inlines = [QuizChoiceInline]
    autocomplete_fields = ("quiz",)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "quiz",
        "score",
        "passed",
        "started_at",
        "completed_at",
        "time_spent_minutes",
    )
    list_filter = ("passed", "quiz__lesson__level__path")
    search_fields = (
        "user__username",
        "user__email",
        "quiz__title",
        "quiz__lesson__title",
    )
    autocomplete_fields = ("user", "quiz")
    readonly_fields = ("started_at", "completed_at")
