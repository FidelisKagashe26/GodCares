from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Post, Season, Series, Lesson, 
    Event, MediaItem, PrayerRequest
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'status', 'featured', 'views', 'created_at']
    list_filter = ['status', 'category', 'featured', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['status', 'featured']
    readonly_fields = ['views', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'author', 'status')
        }),
        ('Content', {
            'fields': ('excerpt', 'content', 'featured_image')
        }),
        ('Settings', {
            'fields': ('featured', 'published_at')
        }),
        ('Metadata', {
            'fields': ('views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new post
            obj.author = request.user
        super().save_model(request, obj, form, change)

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'start_date', 'end_date', 'order', 'created_at']
    list_filter = ['is_active', 'start_date']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'order']

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ['name', 'season', 'order', 'created_at']
    list_filter = ['season', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'series', 'status', 'order', 'views', 'created_at']
    list_filter = ['status', 'series__season', 'series', 'created_at']
    search_fields = ['title', 'content', 'bible_references']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['status', 'order']
    readonly_fields = ['views', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'series', 'status', 'order')
        }),
        ('Content', {
            'fields': ('description', 'content', 'featured_image', 'bible_references', 'duration_minutes')
        }),
        ('Media Files', {
            'fields': ('video_url', 'video_embed_code', 'pdf_file', 'audio_file'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('views', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'location', 'is_featured', 'max_attendees', 'created_at']
    list_filter = ['is_featured', 'date', 'created_at']
    search_fields = ['title', 'description', 'location']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_featured']
    date_hierarchy = 'date'

@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'media_type', 'category', 'views', 'created_at']
    list_filter = ['media_type', 'category', 'created_at']
    search_fields = ['title', 'description', 'tags']
    readonly_fields = ['views', 'created_at']
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="50" height="50" />', obj.thumbnail.url)
        return "No thumbnail"
    thumbnail_preview.short_description = "Thumbnail"

@admin.register(PrayerRequest)
class PrayerRequestAdmin(admin.ModelAdmin):
    list_display = ['get_name', 'category', 'is_urgent', 'is_answered', 'created_at']
    list_filter = ['category', 'is_urgent', 'is_answered', 'is_anonymous', 'created_at']
    search_fields = ['name', 'request']
    readonly_fields = ['created_at']
    list_editable = ['is_answered']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Prayer Request', {
            'fields': ('category', 'request', 'is_anonymous', 'is_urgent')
        }),
        ('Status', {
            'fields': ('is_answered', 'created_at')
        }),
    )
    
    def get_name(self, obj):
        return "Anonymous" if obj.is_anonymous else obj.name or "No name provided"
    get_name.short_description = "Name"
    
    def has_change_permission(self, request, obj=None):
        # Only allow changing the answered status
        return True
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return ['name', 'email', 'phone', 'category', 'request', 'is_anonymous', 'is_urgent', 'created_at']
        return ['created_at']

# Customize admin site
admin.site.site_header = "GOD CARES 365 Administration"
admin.site.site_title = "GOD CARES 365 Admin"
admin.site.index_title = "Content Management System"