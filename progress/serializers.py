# progress/api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model

from progress.models import LessonProgress, LevelProgress

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class LessonProgressSerializer(serializers.ModelSerializer):
    """
    LessonProgress ya progress app (API version).
    Tunaweka ref_name ili isigongane na LessonProgress ya app nyingine.
    """

    user = UserMiniSerializer(read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    level_name = serializers.CharField(source="lesson.level.name", read_only=True)
    path_name = serializers.CharField(source="lesson.level.path.name", read_only=True)
    path_stage = serializers.CharField(source="lesson.level.path.stage", read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id",
            "user",
            "lesson",
            "status",
            "score",
            "completed_at",
            "created_at",
            # extra read-only fields
            "lesson_title",
            "level_name",
            "path_name",
            "path_stage",
        ]
        read_only_fields = ["user", "completed_at", "created_at"]
        ref_name = "ProgressLessonProgress"


class LevelProgressSerializer(serializers.ModelSerializer):
    """
    LevelProgress ya progress app.
    """

    user = UserMiniSerializer(read_only=True)
    level_name = serializers.CharField(source="level.name", read_only=True)
    path_name = serializers.CharField(source="level.path.name", read_only=True)
    path_stage = serializers.CharField(source="level.path.stage", read_only=True)

    class Meta:
        model = LevelProgress
        fields = [
            "id",
            "user",
            "level",
            "status",
            "completed_at",
            "created_at",
            # extra
            "level_name",
            "path_name",
            "path_stage",
        ]
        read_only_fields = ["user", "completed_at", "created_at"]
        ref_name = "ProgressLevelProgress"


# ======== Aggregated / dashboard-style serializers ========


class SimpleUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True, required=False)
    first_name = serializers.CharField(allow_blank=True, required=False)
    last_name = serializers.CharField(allow_blank=True, required=False)


class PathSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    stage = serializers.CharField()
    stage_label = serializers.CharField()


class LevelProgressSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    order = serializers.IntegerField()
    path = PathSummarySerializer()
    total_lessons = serializers.IntegerField()
    percent = serializers.IntegerField()


class ProgressSummarySerializer(serializers.Serializer):
    lessons_completed = serializers.IntegerField()
    total_lessons = serializers.IntegerField()
    overall_percent = serializers.IntegerField()


class MyProgressResponseSerializer(serializers.Serializer):
    user = SimpleUserSerializer()
    levels = LevelProgressSummarySerializer(many=True)
    summary = ProgressSummarySerializer()


class MenteeProgressResponseSerializer(serializers.Serializer):
    mentee = SimpleUserSerializer()
    levels = LevelProgressSummarySerializer(many=True)
    summary = ProgressSummarySerializer()
