# content/api/serializers.py
from rest_framework import serializers
from content.models import (
    Category, Post, Series, Season, Lesson, Event, MediaItem,
    PrayerRequest, LessonComment, Announcement
)

# KUMBUKA:
# - Tumebaki na fields="__all__" ili kuepuka kujitengenezea majina ya field zisizopo.
# - Kwa Lesson tumeweka read_only annotations (likes_count, comments_count, is_liked)
#   ambazo zinatoka kwenye annotate ya ViewSet.

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class PostListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"


class PostDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"


class SeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Series
        fields = "__all__"


class SeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Season
        fields = "__all__"


class LessonListSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(read_only=True, required=False)
    comments_count = serializers.IntegerField(read_only=True, required=False)
    is_liked = serializers.BooleanField(read_only=True, required=False)

    class Meta:
        model = Lesson
        fields = "__all__"


class LessonDetailSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(read_only=True, required=False)
    comments_count = serializers.IntegerField(read_only=True, required=False)
    is_liked = serializers.BooleanField(read_only=True, required=False)

    class Meta:
        model = Lesson
        fields = "__all__"


class EventSerializer(serializers.ModelSerializer):
    # MUHIMU: Event haina 'starts_at' wala 'ends_at'. Tunabaki na fields halisi za model (mf. date, end_date).
    class Meta:
        model = Event
        fields = "__all__"


class MediaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaItem
        fields = "__all__"


class PrayerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerRequest
        fields = "__all__"


class LessonCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonComment
        fields = "__all__"
