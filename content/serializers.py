from rest_framework import serializers
from .models import (
    Category, Post, Season, Series, Lesson, 
    Event, MediaItem, PrayerRequest
)

class CategorySerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'posts_count', 'created_at']
    
    def get_posts_count(self, obj):
        return obj.posts.filter(status='published').count()

class PostListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    read_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'excerpt', 'featured_image', 
            'category', 'author_name', 'featured', 'views', 
            'created_at', 'published_at', 'read_time'
        ]
    
    def get_read_time(self, obj):
        # Estimate reading time (average 200 words per minute)
        word_count = len(obj.content.split())
        return max(1, round(word_count / 200))

class PostDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    read_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'excerpt', 'featured_image',
            'category', 'author_name', 'featured', 'views', 
            'created_at', 'updated_at', 'published_at', 'read_time'
        ]
    
    def get_read_time(self, obj):
        word_count = len(obj.content.split())
        return max(1, round(word_count / 200))

class SeriesListSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    season_name = serializers.CharField(source='season.name', read_only=True)
    
    class Meta:
        model = Series
        fields = ['id', 'name', 'slug', 'description', 'season_name', 'image', 'lessons_count', 'order']
    
    def get_lessons_count(self, obj):
        return obj.lessons.filter(status='published').count()

class SeasonSerializer(serializers.ModelSerializer):
    series = SeriesListSerializer(many=True, read_only=True)
    series_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Season
        fields = [
            'id', 'name', 'slug', 'description', 'image', 
            'start_date', 'end_date', 'is_active', 'order',
            'series', 'series_count', 'created_at'
        ]
    
    def get_series_count(self, obj):
        return obj.series.count()

class LessonListSerializer(serializers.ModelSerializer):
    series_name = serializers.CharField(source='series.name', read_only=True)
    season_name = serializers.CharField(source='series.season.name', read_only=True)
    has_video = serializers.SerializerMethodField()
    has_pdf = serializers.SerializerMethodField()
    has_audio = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'description', 'featured_image',
            'series_name', 'season_name', 'duration_minutes', 'bible_references',
            'has_video', 'has_pdf', 'has_audio', 'order', 'views', 'created_at'
        ]
    
    def get_has_video(self, obj):
        return bool(obj.video_url or obj.video_embed_code)
    
    def get_has_pdf(self, obj):
        return bool(obj.pdf_file)
    
    def get_has_audio(self, obj):
        return bool(obj.audio_file)

class LessonDetailSerializer(serializers.ModelSerializer):
    series = SeriesListSerializer(read_only=True)
    has_video = serializers.SerializerMethodField()
    has_pdf = serializers.SerializerMethodField()
    has_audio = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'description', 'content', 'featured_image',
            'series', 'video_url', 'video_embed_code', 'pdf_file', 'audio_file',
            'duration_minutes', 'bible_references', 'has_video', 'has_pdf', 
            'has_audio', 'order', 'views', 'created_at', 'updated_at'
        ]
    
    def get_has_video(self, obj):
        return bool(obj.video_url or obj.video_embed_code)
    
    def get_has_pdf(self, obj):
        return bool(obj.pdf_file)
    
    def get_has_audio(self, obj):
        return bool(obj.audio_file)

class EventSerializer(serializers.ModelSerializer):
    is_upcoming = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'description', 'location', 
            'date', 'end_date', 'image', 'registration_url',
            'is_featured', 'max_attendees', 'is_upcoming', 'created_at'
        ]
    
    def get_is_upcoming(self, obj):
        from django.utils import timezone
        return obj.date > timezone.now()

class MediaItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = MediaItem
        fields = [
            'id', 'title', 'description', 'media_type', 'file', 'url',
            'thumbnail', 'category_name', 'tags', 'views', 'created_at'
        ]

class PrayerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrayerRequest
        fields = [
            'id', 'name', 'email', 'phone', 'category', 'request',
            'is_anonymous', 'is_urgent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        # If anonymous, clear personal information
        if validated_data.get('is_anonymous', False):
            validated_data['name'] = ''
            validated_data['email'] = ''
            validated_data['phone'] = ''
        return super().create(validated_data)