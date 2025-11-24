# discipleship/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field

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


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class DiscipleshipPathSerializer(serializers.ModelSerializer):
    levels_count = serializers.SerializerMethodField()
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)

    class Meta:
        model = DiscipleshipPath
        fields = [
            "id",
            "name",
            "stage",
            "stage_display",
            "slug",
            "description",
            "image",
            "order",
            "is_active",
            "levels_count",
            "created_at",
        ]

    @extend_schema_field(serializers.IntegerField)
    def get_levels_count(self, obj) -> int:
        return obj.levels.count()


class DiscipleshipLevelSerializer(serializers.ModelSerializer):
    path_name = serializers.CharField(source="path.name", read_only=True)
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = DiscipleshipLevel
        fields = [
            "id",
            "path",
            "path_name",
            "name",
            "slug",
            "description",
            "order",
            "required_score",
            "is_active",
            "lessons_count",
            "created_at",
        ]

    @extend_schema_field(serializers.IntegerField)
    def get_lessons_count(self, obj) -> int:
        return obj.lessons.filter(is_published=True).count()


class DiscipleshipLessonListSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source="level.name", read_only=True)
    path_name = serializers.CharField(source="level.path.name", read_only=True)
    path_stage = serializers.CharField(source="level.path.stage", read_only=True)
    has_video = serializers.SerializerMethodField()
    has_audio = serializers.SerializerMethodField()
    has_pdf = serializers.SerializerMethodField()

    class Meta:
        model = DiscipleshipLesson
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "level",
            "level_name",
            "path_name",
            "path_stage",
            "duration_minutes",
            "bible_references",
            "order",
            "points_value",
            "is_published",
            "has_video",
            "has_audio",
            "has_pdf",
            "created_at",
        ]

    @extend_schema_field(serializers.BooleanField)
    def get_has_video(self, obj) -> bool:
        # DiscipleshipLesson ina video_url tu, hakuna embed_code
        return bool(getattr(obj, "video_url", None))

    @extend_schema_field(serializers.BooleanField)
    def get_has_audio(self, obj) -> bool:
        return bool(getattr(obj, "audio_url", None))

    @extend_schema_field(serializers.BooleanField)
    def get_has_pdf(self, obj) -> bool:
        return bool(getattr(obj, "pdf_file", None))


class DiscipleshipLessonDetailSerializer(serializers.ModelSerializer):
    level = DiscipleshipLevelSerializer(read_only=True)
    has_video = serializers.SerializerMethodField()
    has_audio = serializers.SerializerMethodField()
    has_pdf = serializers.SerializerMethodField()

    class Meta:
        model = DiscipleshipLesson
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "content",
            "level",
            "video_url",
            "audio_url",
            "pdf_file",
            "duration_minutes",
            "bible_references",
            "order",
            "points_value",
            "is_published",
            "requires_previous",
            "has_video",
            "has_audio",
            "has_pdf",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.BooleanField)
    def get_has_video(self, obj) -> bool:
        return bool(getattr(obj, "video_url", None))

    @extend_schema_field(serializers.BooleanField)
    def get_has_audio(self, obj) -> bool:
        return bool(getattr(obj, "audio_url", None))

    @extend_schema_field(serializers.BooleanField)
    def get_has_pdf(self, obj) -> bool:
        return bool(getattr(obj, "pdf_file", None))


class LessonProgressSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    lesson_slug = serializers.CharField(source="lesson.slug", read_only=True)
    level_name = serializers.CharField(source="lesson.level.name", read_only=True)
    path_name = serializers.CharField(source="lesson.level.path.name", read_only=True)
    path_stage = serializers.CharField(source="lesson.level.path.stage", read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "user",
            "lesson",
            "lesson_title",
            "lesson_slug",
            "level_name",
            "path_name",
            "path_stage",
            "status",
            "started_at",
            "completed_at",
            "score",
            "notes",
            "time_spent_minutes",
            "last_accessed",
            "created_at",
        ]
        read_only_fields = [
            "user",
            "started_at",
            "completed_at",
            "last_accessed",
            "created_at",
        ]


class PathEnrollmentSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    path_name = serializers.CharField(source="path.name", read_only=True)
    path_stage = serializers.CharField(source="path.stage", read_only=True)
    current_level_name = serializers.CharField(
        source="current_level.name",
        read_only=True,
    )

    class Meta:
        model = PathEnrollment
        fields = [
            "id",
            "user",
            "path",
            "path_name",
            "path_stage",
            "current_level",
            "current_level_name",
            "enrolled_at",
            "completed_at",
            "is_active",
            "progress_percentage",
        ]
        read_only_fields = ["user", "enrolled_at", "completed_at", "progress_percentage"]


class QuizChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizChoice
        fields = ["id", "choice_text", "is_correct", "order"]
        extra_kwargs = {"is_correct": {"write_only": True}}


class QuizQuestionSerializer(serializers.ModelSerializer):
    choices = QuizChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "quiz",
            "question_type",
            "question_text",
            "explanation",
            "order",
            "points",
            "choices",
        ]


class QuizSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "lesson",
            "lesson_title",
            "title",
            "description",
            "passing_score",
            "time_limit_minutes",
            "max_attempts",
            "is_active",
            "questions",
            "created_at",
        ]


class QuizAttemptSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)
    lesson_title = serializers.CharField(source="quiz.lesson.title", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "user",
            "quiz",
            "quiz_title",
            "lesson_title",
            "score",
            "passed",
            "started_at",
            "completed_at",
            "time_spent_minutes",
            "answers",
        ]
        read_only_fields = ["user", "started_at", "completed_at"]
