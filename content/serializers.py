# content/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    Category,
    Post,
    Season,
    Series,
    Lesson,
    Event,
    MediaItem,
    PrayerRequest,
    LessonLike,
    LessonComment,
    Announcement,
    Profile,
    SiteSetting,
    DiscipleshipJourney,
    StageProgress,
    MissionReport,
    BibleStudyGroup,
    BaptismRecord,
    MissionMapLocation,
    Certificate,
    GlobalSoulsCounter,
)

# ==================== USER & AUTH SERIALIZERS ====================


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "date_joined",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = "__all__"


# ==================== CONTENT SERIALIZERS ====================


class CategorySerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "posts_count", "created_at"]

    def get_posts_count(self, obj):
        return obj.posts.filter(status="published").count()


class PostListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author_name = serializers.CharField(
        source="author.get_full_name",
        read_only=True,
    )
    read_time = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "featured_image",
            "category",
            "author_name",
            "featured",
            "views",
            "created_at",
            "published_at",
            "read_time",
        ]

    def get_read_time(self, obj):
        word_count = len((obj.content or "").split())
        return max(1, round(word_count / 200))


class PostDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author_name = serializers.CharField(
        source="author.get_full_name",
        read_only=True,
    )
    read_time = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "slug",
            "content",
            "excerpt",
            "featured_image",
            "category",
            "author_name",
            "featured",
            "views",
            "created_at",
            "updated_at",
            "published_at",
            "read_time",
        ]

    def get_read_time(self, obj):
        word_count = len((obj.content or "").split())
        return max(1, round(word_count / 200))


class SeriesSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    season_name = serializers.CharField(source="season.name", read_only=True)

    class Meta:
        model = Series
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "season_name",
            "image",
            "lessons_count",
            "order",
        ]

    def get_lessons_count(self, obj):
        return obj.lessons.filter(status="published").count()


class SeasonSerializer(serializers.ModelSerializer):
    series = SeriesSerializer(many=True, read_only=True)
    series_count = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "start_date",
            "end_date",
            "is_active",
            "order",
            "series",
            "series_count",
            "created_at",
        ]

    def get_series_count(self, obj):
        return obj.series.count()


class LessonListSerializer(serializers.ModelSerializer):
    series_name = serializers.CharField(source="series.name", read_only=True)
    season_name = serializers.CharField(source="series.season.name", read_only=True)
    has_video = serializers.SerializerMethodField()
    has_pdf = serializers.SerializerMethodField()
    has_audio = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "featured_image",
            "series_name",
            "season_name",
            "duration_minutes",
            "bible_references",
            "has_video",
            "has_pdf",
            "has_audio",
            "order",
            "views",
            "created_at",
        ]

    def get_has_video(self, obj):
        return bool(getattr(obj, "video_url", None) or getattr(obj, "video_embed_code", None))

    def get_has_pdf(self, obj):
        return bool(getattr(obj, "pdf_file", None))

    def get_has_audio(self, obj):
        return bool(getattr(obj, "audio_file", None))


class LessonDetailSerializer(serializers.ModelSerializer):
    series = SeriesSerializer(read_only=True)
    has_video = serializers.SerializerMethodField()
    has_pdf = serializers.SerializerMethodField()
    has_audio = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "content",
            "featured_image",
            "series",
            "video_url",
            "video_embed_code",
            "pdf_file",
            "audio_file",
            "duration_minutes",
            "bible_references",
            "has_video",
            "has_pdf",
            "has_audio",
            "order",
            "views",
            "created_at",
            "updated_at",
        ]

    def get_has_video(self, obj):
        return bool(getattr(obj, "video_url", None) or getattr(obj, "video_embed_code", None))

    def get_has_pdf(self, obj):
        return bool(getattr(obj, "pdf_file", None))

    def get_has_audio(self, obj):
        return bool(getattr(obj, "audio_file", None))


class EventSerializer(serializers.ModelSerializer):
    is_upcoming = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "location",
            "date",
            "end_date",
            "image",
            "registration_url",
            "is_featured",
            "max_attendees",
            "is_upcoming",
            "created_at",
        ]

    def get_is_upcoming(self, obj):
        from django.utils import timezone

        if not obj.date:
            return False
        return obj.date > timezone.now()


class MediaItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = MediaItem
        fields = [
            "id",
            "title",
            "description",
            "media_type",
            "file",
            "url",
            "thumbnail",
            "category_name",
            "tags",
            "views",
            "created_at",
        ]


class PrayerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerRequest
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "category",
            "request",
            "is_anonymous",
            "is_urgent",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        if validated_data.get("is_anonymous", False):
            validated_data["name"] = ""
            validated_data["email"] = ""
            validated_data["phone"] = ""
        return super().create(validated_data)


class LessonCommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = LessonComment
        fields = [
            "id",
            "user",
            "user_name",
            "user_username",
            "lesson",
            "body",
            "is_approved",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]


class LessonLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonLike
        fields = ["id", "user", "lesson", "created_at"]
        read_only_fields = ["user", "created_at"]


class AnnouncementSerializer(serializers.ModelSerializer):
    sent_by_name = serializers.CharField(source="sent_by.get_full_name", read_only=True)

    class Meta:
        model = Announcement
        fields = ["id", "title", "body", "sent_by", "sent_by_name", "sent_at", "created_at"]


class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = "__all__"


# ==================== MISSION PLATFORM SERIALIZERS ====================


class DiscipleshipJourneySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    current_stage_display = serializers.CharField(
        source="get_current_stage_display",
        read_only=True,
    )

    class Meta:
        model = DiscipleshipJourney
        fields = "__all__"


class StageProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    lesson_slug = serializers.CharField(source="lesson.slug", read_only=True)

    class Meta:
        model = StageProgress
        fields = "__all__"


class MissionReportSerializer(serializers.ModelSerializer):
    missionary_name = serializers.CharField(
        source="missionary.get_full_name",
        read_only=True,
    )
    verified_by_name = serializers.CharField(
        source="verified_by.get_full_name",
        read_only=True,
        allow_null=True,
        default="",
    )

    class Meta:
        model = MissionReport
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class BibleStudyGroupSerializer(serializers.ModelSerializer):
    leader_name = serializers.CharField(source="leader.get_full_name", read_only=True)
    member_count = serializers.SerializerMethodField()
    current_lesson_title = serializers.CharField(
        source="current_lesson.title",
        read_only=True,
    )

    class Meta:
        model = BibleStudyGroup
        fields = "__all__"

    def get_member_count(self, obj):
        # +1 kwa ajili ya leader mwenyewe
        return obj.members.count() + 1


class BaptismRecordSerializer(serializers.ModelSerializer):
    missionary_name = serializers.CharField(
        source="missionary.get_full_name",
        read_only=True,
    )

    class Meta:
        model = BaptismRecord
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class MissionMapLocationSerializer(serializers.ModelSerializer):
    missionary_name = serializers.CharField(
        source="missionary.get_full_name",
        read_only=True,
    )
    visit_type_display = serializers.CharField(
        source="get_visit_type_display",
        read_only=True,
    )

    class Meta:
        model = MissionMapLocation
        fields = "__all__"
        read_only_fields = ["created_at"]


class CertificateSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    certificate_type_display = serializers.CharField(
        source="get_certificate_type_display",
        read_only=True,
    )
    issued_by_name = serializers.CharField(
        source="issued_by.get_full_name",
        read_only=True,
    )

    class Meta:
        model = Certificate
        fields = "__all__"
        read_only_fields = ["created_at"]


class GlobalSoulsCounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalSoulsCounter
        fields = "__all__"
