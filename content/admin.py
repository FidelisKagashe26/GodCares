from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    Category, Post, Season, Series, Lesson, Event, MediaItem, PrayerRequest,
    LessonLike, LessonComment, Announcement, Profile, SiteSettings
)

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # ruhusu 1 tu
        return not SiteSettings.objects.exists() or super().has_add_permission(request)
    
# ===========================
# Inlines for Lesson
# ===========================
class LessonCommentInline(admin.TabularInline):
    model = LessonComment
    extra = 0
    fields = ("user", "body", "is_approved", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True


class LessonLikeInline(admin.TabularInline):
    model = LessonLike
    extra = 0
    fields = ("user", "created_at")
    readonly_fields = ("created_at",)
    can_delete = True


# ===========================
# Category
# ===========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]
    ordering = ["name"]


# ===========================
# Post
# ===========================
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "author", "status", "featured", "views", "published_at", "created_at"]
    list_filter = ["status", "category", "featured", "created_at", "published_at"]
    search_fields = ["title", "content", "excerpt"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["status", "featured"]
    readonly_fields = ["views", "created_at", "updated_at"]
    date_hierarchy = "published_at"

    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "slug", "category", "author", "status", "featured")
        }),
        ("Content", {
            "fields": ("excerpt", "content", "featured_image")
        }),
        ("Publishing", {
            "fields": ("published_at",),
        }),
        ("Metadata", {
            "fields": ("views", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)


# ===========================
# Season
# ===========================
@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "start_date", "end_date", "order", "created_at"]
    list_filter = ["is_active", "start_date"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["is_active", "order"]
    ordering = ["order", "-created_at"]


# ===========================
# Series
# ===========================
@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ["name", "season", "order", "created_at"]
    list_filter = ["season", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["order"]
    ordering = ["season", "order", "-created_at"]


# ===========================
# Lesson
# ===========================
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "series", "status", "order", "views", "like_count_col", "comment_count_col", "published_at", "created_at"]
    list_filter = ["status", "series__season", "series", "created_at", "published_at"]
    search_fields = ["title", "content", "bible_references", "description"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["status", "order"]
    readonly_fields = ["views", "created_at", "updated_at", "published_at"]
    inlines = [LessonCommentInline, LessonLikeInline]
    date_hierarchy = "published_at"
    actions = ["publish_selected", "unpublish_selected", "email_subscribers"]

    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "slug", "series", "status", "order")
        }),
        ("Content", {
            "fields": ("description", "content", "featured_image", "bible_references", "duration_minutes")
        }),
        ("Media Files", {
            "fields": ("video_url", "video_embed_code", "pdf_file", "audio_file"),
            "classes": ("collapse",)
        }),
        ("Publishing", {
            "fields": ("published_at",),
        }),
        ("Metadata", {
            "fields": ("views", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    # Columns
    def like_count_col(self, obj):
        return obj.like_count
    like_count_col.short_description = "Likes"

    def comment_count_col(self, obj):
        return obj.comment_count
    comment_count_col.short_description = "Comments"

    # Actions
    def publish_selected(self, request, queryset):
        updated = 0
        now = timezone.now()
        for lesson in queryset:
            if lesson.status != "published":
                lesson.status = "published"
                if not lesson.published_at:
                    lesson.published_at = now
                lesson.save()
                updated += 1
        self.message_user(request, f"Published {updated} lesson(s).", level=messages.SUCCESS)

    publish_selected.short_description = "Publish selected lessons"

    def unpublish_selected(self, request, queryset):
        updated = queryset.update(status="draft")
        self.message_user(request, f"Moved {updated} lesson(s) to Draft.", level=messages.INFO)

    unpublish_selected.short_description = "Unpublish selected lessons"

    def email_subscribers(self, request, queryset):
        from .utils.emailing import send_lesson_published_email_to_subscribers
        sent = 0
        for lesson in queryset:
            if lesson.status == "published":
                send_lesson_published_email_to_subscribers(lesson)
                sent += 1
        self.message_user(request, f"Emails sent for {sent} published lesson(s).", level=messages.SUCCESS)

    email_subscribers.short_description = "Email subscribers about selected lessons"


# ===========================
# Event
# ===========================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "location", "is_featured", "max_attendees", "created_at"]
    list_filter = ["is_featured", "date", "created_at"]
    search_fields = ["title", "description", "location"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["is_featured"]
    date_hierarchy = "date"


# ===========================
# MediaItem
# ===========================
@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ["title", "media_type", "category", "views", "thumbnail_preview", "created_at"]
    list_filter = ["media_type", "category", "created_at"]
    search_fields = ["title", "description", "tags"]
    readonly_fields = ["views", "created_at"]

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover;border-radius:6px;" />', obj.thumbnail.url)
        return "—"
    thumbnail_preview.short_description = "Thumbnail"


# ===========================
# PrayerRequest
# ===========================
@admin.register(PrayerRequest)
class PrayerRequestAdmin(admin.ModelAdmin):
    list_display = ["get_name", "category", "is_urgent", "is_answered", "created_at"]
    list_filter = ["category", "is_urgent", "is_answered", "is_anonymous", "created_at"]
    search_fields = ["name", "request", "email", "phone"]
    readonly_fields = ["created_at"]
    list_editable = ["is_answered"]

    fieldsets = (
        ("Contact Information", {
            "fields": ("name", "email", "phone")
        }),
        ("Prayer Request", {
            "fields": ("category", "request", "is_anonymous", "is_urgent")
        }),
        ("Status", {
            "fields": ("is_answered", "created_at")
        }),
    )

    def get_name(self, obj):
        return "Anonymous" if obj.is_anonymous else (obj.name or "No name provided")
    get_name.short_description = "Name"

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return ["name", "email", "phone", "category", "request", "is_anonymous", "is_urgent", "created_at"]
        return ["created_at"]


# ===========================
# Likes & Comments
# ===========================
@admin.register(LessonLike)
class LessonLikeAdmin(admin.ModelAdmin):
    list_display = ["user", "lesson", "created_at"]
    list_filter = ["lesson", "user", "created_at"]
    search_fields = ["user__username", "lesson__title"]
    readonly_fields = ["created_at"]


@admin.register(LessonComment)
class LessonCommentAdmin(admin.ModelAdmin):
    list_display = ["user", "lesson", "short_body", "is_approved", "created_at"]
    list_filter = ["is_approved", "lesson", "user", "created_at"]
    search_fields = ["user__username", "lesson__title", "body"]
    list_editable = ["is_approved"]
    readonly_fields = ["created_at"]

    def short_body(self, obj):
        return (obj.body[:80] + "…") if len(obj.body) > 80 else obj.body
    short_body.short_description = "Comment"


# ===========================
# Announcement
# ===========================
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "sent_at", "created_at", "sent_by"]
    search_fields = ["title", "body"]
    actions = ["send_to_subscribers"]

    def send_to_subscribers(self, request, queryset):
        from .utils.emailing import _send_html_email
        from django.contrib.auth.models import User

        subscribers = User.objects.filter(profile__receive_notifications=True).select_related("profile")
        total = 0
        for ann in queryset:
            for u in subscribers:
                _send_html_email(
                    subject=ann.title,
                    to_email=u.email,
                    template_name="emails/announcement.html",
                    context={"user": u, "title": ann.title, "body": ann.body, "site_name": "GOD CARES 365"},
                )
                total += 1
            ann.sent_at = timezone.now()
            ann.sent_by = request.user
            ann.save()
        self.message_user(request, f"Announcement emails queued/sent: {total}.", level=messages.SUCCESS)

    send_to_subscribers.short_description = "Send announcement to subscribers"


# ===========================
# Profile
# ===========================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "email_verified", "phone_number", "receive_notifications", "created_at"]
    list_filter = ["email_verified", "receive_notifications", "created_at"]
    search_fields = ["user__username", "user__email", "phone_number"]
    readonly_fields = ["created_at"]


# ===========================
# Admin branding
# ===========================
admin.site.site_header = "GOD CARES 365 Administration"
admin.site.site_title = "GOD CARES 365 Admin"
admin.site.index_title = "Content Management System"
