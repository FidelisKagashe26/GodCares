# content/admin.py
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse, path
from django.db.models import Count, Sum, Q
from django.contrib.auth.models import User
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from .models import (
    Category, Post, Season, Series, Lesson, Event, MediaItem, PrayerRequest,
    LessonLike, LessonComment, Announcement, Profile, SiteSetting,
    DiscipleshipJourney, StageProgress, MissionReport, BibleStudyGroup,
    BaptismRecord, MissionMapLocation, Certificate, GlobalSoulsCounter
)

# ===========================
# Custom Admin Site
# ===========================
class GodCares365AdminSite(admin.AdminSite):
    site_header = "🌍 GOD CARES 365 Mission Platform"
    site_title = "GOD CARES 365 Admin"
    index_title = "Mission Dashboard"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('mission-stats/', self.admin_view(self.mission_stats_view), name='mission-stats'),
            path('global-dashboard/', self.admin_view(self.global_dashboard_view), name='global-dashboard'),
        ]
        return custom_urls + urls
    
    def mission_stats_view(self, request):
        """Custom view for mission statistics"""
        global_stats = GlobalSoulsCounter.objects.first()
        if not global_stats:
            global_stats = GlobalSoulsCounter.objects.create(pk=1)
        
        # Recent mission reports
        recent_missions = MissionReport.objects.select_related('missionary').order_by('-created_at')[:10]
        
        # Top missionaries
        top_missionaries = User.objects.annotate(
            total_souls=Sum('mission_reports__souls_reached'),
            total_missions=Count('mission_reports')
        ).filter(total_souls__gt=0).order_by('-total_souls')[:10]
        
        context = {
            **self.each_context(request),
            'global_stats': global_stats,
            'recent_missions': recent_missions,
            'top_missionaries': top_missionaries,
            'title': 'Mission Statistics'
        }
        return render(request, 'admin/mission_stats.html', context)
    
    def global_dashboard_view(self, request):
        """Global dashboard view"""
        global_stats = GlobalSoulsCounter.objects.first()
        if not global_stats:
            global_stats = GlobalSoulsCounter.objects.create(pk=1)
        
        # Discipleship progress
        journey_stats = DiscipleshipJourney.objects.aggregate(
            total_users=Count('id'),
            seekers=Count('id', filter=Q(current_stage='seeker')),
            scholars=Count('id', filter=Q(current_stage='scholar')),
            missionaries=Count('id', filter=Q(current_stage='missionary')),
            completed=Count('id', filter=Q(missionary_completed=True))
        )
        
        # Recent activity
        recent_baptisms = BaptismRecord.objects.select_related('missionary').order_by('-baptism_date')[:10]
        active_groups = BibleStudyGroup.objects.filter(is_active=True).count()
        
        context = {
            **self.each_context(request),
            'global_stats': global_stats,
            'journey_stats': journey_stats,
            'recent_baptisms': recent_baptisms,
            'active_groups': active_groups,
            'title': 'Global Mission Dashboard'
        }
        return render(request, 'admin/global_dashboard.html', context)

# ===========================
# Inlines (ONLY FOR MODELS WITH FOREIGN KEYS)
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

class StageProgressInline(admin.TabularInline):
    model = StageProgress
    extra = 0
    fields = ("lesson", "completed", "score", "completed_date")
    readonly_fields = ("completed_date",)

# ===========================
# Global Souls Counter Admin
# ===========================
@admin.register(GlobalSoulsCounter)
class GlobalSoulsCounterAdmin(admin.ModelAdmin):
    list_display = [
        'total_souls_reached', 'total_baptisms', 'total_mission_reports',
        'total_bible_study_groups', 'active_missionaries', 'last_updated'
    ]
    readonly_fields = ['last_updated']
    actions = ['refresh_stats']

    def has_add_permission(self, request):
        return not GlobalSoulsCounter.objects.exists()

    def changelist_view(self, request, extra_context=None):
        try:
            obj = GlobalSoulsCounter.objects.get(pk=1)
            return HttpResponseRedirect(reverse("admin:content_globalsoulscounter_change", args=(obj.pk,)))
        except GlobalSoulsCounter.DoesNotExist:
            return HttpResponseRedirect(reverse("admin:content_globalsoulscounter_add"))

    def refresh_stats(self, request, queryset):
        """Refresh global statistics"""
        from .signals import update_global_souls_counter
        update_global_souls_counter()
        self.message_user(request, "Global statistics refreshed successfully.", messages.SUCCESS)
    refresh_stats.short_description = "Refresh global statistics"

# ===========================
# Content Admins
# ===========================
@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ["site_name", "contact_email", "contact_phone", "email_from_address"]
    fieldsets = (
        ("Basic Information", {
            "fields": ("site_name", "tagline")
        }),
        ("Contact Information", {
            "fields": ("contact_email", "contact_phone", "address")
        }),
        ("Social Media", {
            "fields": ("facebook_url", "twitter_url", "instagram_url")
        }),
        ("Email Settings", {
            "fields": ("email_from_name", "email_from_address")
        }),
        ("Other Settings", {
            "fields": ("footer_about", "notifications_opt_in_default")
        }),
    )
    
    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def changelist_view(self, request, extra_context=None):
        try:
            obj = SiteSetting.objects.get(pk=1)
            return HttpResponseRedirect(reverse("admin:content_sitesetting_change", args=(obj.pk,)))
        except SiteSetting.DoesNotExist:
            return HttpResponseRedirect(reverse("admin:content_sitesetting_add"))

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "posts_count", "created_at"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]
    ordering = ["name"]

    def posts_count(self, obj):
        return obj.posts.count()
    posts_count.short_description = "Posts"

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

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "series_count", "start_date", "end_date", "order", "created_at"]
    list_filter = ["is_active", "start_date"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["is_active", "order"]
    ordering = ["order", "-created_at"]

    def series_count(self, obj):
        return obj.series.count()
    series_count.short_description = "Series"

@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ["name", "season", "lessons_count", "order", "created_at"]
    list_filter = ["season", "created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ["order"]
    ordering = ["season", "order", "-created_at"]

    def lessons_count(self, obj):
        return obj.lessons.count()
    lessons_count.short_description = "Lessons"

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "series", "status", "order", "views", "like_count", "comment_count", "published_at", "created_at"]
    list_filter = ["status", "series__season", "series", "created_at", "published_at"]
    search_fields = ["title", "content", "bible_references", "description"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["status", "order"]
    readonly_fields = ["views", "created_at", "updated_at", "published_at"]
    inlines = [LessonCommentInline, LessonLikeInline]
    date_hierarchy = "published_at"
    actions = ["publish_selected", "unpublish_selected"]

    def like_count(self, obj):
        return obj.lesson_likes.count()
    like_count.short_description = "Likes"

    def comment_count(self, obj):
        return obj.lesson_comments.filter(is_approved=True).count()
    comment_count.short_description = "Comments"

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
        self.message_user(request, f"Published {updated} lesson(s).", messages.SUCCESS)
    publish_selected.short_description = "Publish selected lessons"

    def unpublish_selected(self, request, queryset):
        updated = queryset.update(status="draft")
        self.message_user(request, f"Moved {updated} lesson(s) to Draft.", messages.INFO)
    unpublish_selected.short_description = "Unpublish selected lessons"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "location", "is_featured", "max_attendees", "created_at"]
    list_filter = ["is_featured", "date", "created_at"]
    search_fields = ["title", "description", "location"]
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["is_featured"]
    date_hierarchy = "date"

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

@admin.register(PrayerRequest)
class PrayerRequestAdmin(admin.ModelAdmin):
    list_display = ["get_name", "category", "is_urgent", "is_answered", "created_at"]
    list_filter = ["category", "is_urgent", "is_answered", "is_anonymous", "created_at"]
    search_fields = ["name", "request", "email", "phone"]
    readonly_fields = ["created_at"]
    list_editable = ["is_answered"]
    actions = ["mark_as_answered", "mark_as_urgent"]

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
        if obj:
            return ["name", "email", "phone", "category", "request", "is_anonymous", "is_urgent", "created_at"]
        return ["created_at"]

    def mark_as_answered(self, request, queryset):
        updated = queryset.update(is_answered=True)
        self.message_user(request, f"Marked {updated} prayer request(s) as answered.", messages.SUCCESS)
    mark_as_answered.short_description = "Mark selected as answered"

    def mark_as_urgent(self, request, queryset):
        updated = queryset.update(is_urgent=True)
        self.message_user(request, f"Marked {updated} prayer request(s) as urgent.", messages.SUCCESS)
    mark_as_urgent.short_description = "Mark selected as urgent"

# ===========================
# Mission Platform Admins
# ===========================
@admin.register(DiscipleshipJourney)
class DiscipleshipJourneyAdmin(admin.ModelAdmin):
    list_display = ["user", "current_stage_display", "progress_percentage", "seeker_completed", "scholar_completed", "missionary_completed", "started_date"]
    list_filter = ["current_stage", "seeker_completed", "scholar_completed", "missionary_completed"]
    search_fields = ["user__username", "user__email", "user__first_name", "user__last_name"]
    readonly_fields = ["started_date", "completed_date"]
    inlines = [StageProgressInline]
    actions = ["advance_to_next_stage", "reset_progress"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def current_stage_display(self, obj):
        stage_icons = {
            'seeker': '📘',
            'scholar': '📖', 
            'missionary': '🌍'
        }
        return f"{stage_icons.get(obj.current_stage, '')} {obj.get_current_stage_display()}"
    current_stage_display.short_description = "Current Stage"

    def advance_to_next_stage(self, request, queryset):
        for journey in queryset:
            if journey.current_stage == 'seeker':
                journey.current_stage = 'scholar'
                journey.seeker_completed = True
            elif journey.current_stage == 'scholar':
                journey.current_stage = 'missionary'
                journey.scholar_completed = True
            elif journey.current_stage == 'missionary':
                journey.missionary_completed = True
                journey.completed_date = timezone.now()
            journey.save()
        self.message_user(request, "Advanced selected journeys to next stage.", messages.SUCCESS)
    advance_to_next_stage.short_description = "Advance to next stage"

    def reset_progress(self, request, queryset):
        queryset.update(
            current_stage='seeker',
            progress_percentage=0,
            seeker_completed=False,
            scholar_completed=False,
            missionary_completed=False,
            completed_date=None
        )
        self.message_user(request, "Reset progress for selected journeys.", messages.SUCCESS)
    reset_progress.short_description = "Reset progress"

@admin.register(StageProgress)
class StageProgressAdmin(admin.ModelAdmin):
    list_display = ["journey_user", "stage", "lesson", "completed", "score", "completed_date"]
    list_filter = ["stage", "completed", "journey__current_stage"]
    search_fields = ["journey__user__username", "lesson__title"]
    readonly_fields = ["completed_date"]
    actions = ["mark_as_completed"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('journey__user', 'lesson')

    def journey_user(self, obj):
        return obj.journey.user
    journey_user.short_description = "User"

    def mark_as_completed(self, request, queryset):
        for progress in queryset:
            progress.completed = True
            progress.completed_date = timezone.now()
            progress.score = 100
            progress.save()
        self.message_user(request, "Marked selected progress as completed.", messages.SUCCESS)
    mark_as_completed.short_description = "Mark as completed"

@admin.register(MissionReport)
class MissionReportAdmin(admin.ModelAdmin):
    list_display = ["missionary", "title", "location", "date_conducted", "souls_reached", "baptisms_performed", "is_verified", "created_at"]
    list_filter = ["is_verified", "date_conducted", "created_at"]
    search_fields = ["missionary__username", "title", "location", "testimonies"]
    readonly_fields = ["created_at", "updated_at", "verified_at"]
    actions = ["verify_reports", "export_reports"]

    fieldsets = (
        ("Basic Information", {
            "fields": ("missionary", "title", "location", "date_conducted")
        }),
        ("Mission Details", {
            "fields": ("souls_reached", "testimonies", "challenges", "lessons_learned")
        }),
        ("Baptism Records", {
            "fields": ("baptisms_performed", "baptism_details"),
            "classes": ("collapse",)
        }),
        ("Media Evidence", {
            "fields": ("photos", "videos"),
            "classes": ("collapse",)
        }),
        ("GPS & Location", {
            "fields": ("gps_coordinates",),
            "classes": ("collapse",)
        }),
        ("Verification", {
            "fields": ("is_verified", "verified_by", "verified_at"),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('missionary', 'verified_by')

    def verify_reports(self, request, queryset):
        for report in queryset:
            report.is_verified = True
            report.verified_by = request.user
            report.verified_at = timezone.now()
            report.save()
        self.message_user(request, f"Verified {queryset.count()} mission report(s).", messages.SUCCESS)
    verify_reports.short_description = "Verify selected reports"

    def export_reports(self, request, queryset):
        # This would typically generate a CSV or PDF export
        self.message_user(request, f"Preparing export for {queryset.count()} report(s)...", messages.INFO)
    export_reports.short_description = "Export selected reports"

@admin.register(BibleStudyGroup)
class BibleStudyGroupAdmin(admin.ModelAdmin):
    list_display = ["group_name", "leader", "meeting_frequency", "member_count", "is_active", "created_at"]
    list_filter = ["is_active", "meeting_frequency", "created_at"]
    search_fields = ["group_name", "leader__username", "location", "description"]
    readonly_fields = ["created_at", "updated_at"]
    actions = ["activate_groups", "deactivate_groups"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('leader', 'current_lesson')

    def member_count(self, obj):
        return obj.members.count() + 1  # +1 for leader
    member_count.short_description = "Members"

    def activate_groups(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Activated {queryset.count()} group(s).", messages.SUCCESS)
    activate_groups.short_description = "Activate selected groups"

    def deactivate_groups(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {queryset.count()} group(s).", messages.SUCCESS)
    deactivate_groups.short_description = "Deactivate selected groups"

@admin.register(BaptismRecord)
class BaptismRecordAdmin(admin.ModelAdmin):
    list_display = ["candidate_name", "missionary", "baptism_date", "location", "follow_up_completed", "created_at"]
    list_filter = ["baptism_date", "follow_up_completed", "created_at"]
    search_fields = ["candidate_name", "missionary__username", "location"]
    readonly_fields = ["created_at", "updated_at"]
    actions = ["mark_follow_up_completed"]

    fieldsets = (
        ("Candidate Information", {
            "fields": ("candidate_name", "candidate_age", "candidate_contact", "candidate_email")
        }),
        ("Baptism Details", {
            "fields": ("missionary", "baptism_date", "location", "baptism_notes")
        }),
        ("Spiritual Background", {
            "fields": ("previous_religion", "testimony"),
            "classes": ("collapse",)
        }),
        ("Follow-up", {
            "fields": ("follow_up_plan", "follow_up_completed"),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('missionary')

    def mark_follow_up_completed(self, request, queryset):
        queryset.update(follow_up_completed=True)
        self.message_user(request, f"Marked {queryset.count()} baptism record(s) as follow-up completed.", messages.SUCCESS)
    mark_follow_up_completed.short_description = "Mark follow-up completed"

@admin.register(MissionMapLocation)
class MissionMapLocationAdmin(admin.ModelAdmin):
    list_display = ["missionary", "location_name", "date_visited", "visit_type", "souls_contacted", "created_at"]
    list_filter = ["visit_type", "date_visited", "created_at"]
    search_fields = ["missionary__username", "location_name", "notes"]
    readonly_fields = ["created_at"]
    actions = ["export_locations"]

    fieldsets = (
        ("Location Information", {
            "fields": ("missionary", "location_name", "gps_coordinates")
        }),
        ("Visit Details", {
            "fields": ("date_visited", "visit_type", "souls_contacted", "notes")
        }),
        ("Media", {
            "fields": ("photos",),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("created_at",),
            "classes": ("collapse",)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('missionary')

    def export_locations(self, request, queryset):
        # This would typically generate a KML or CSV file for maps
        self.message_user(request, f"Preparing export for {queryset.count()} location(s)...", messages.INFO)
    export_locations.short_description = "Export locations for mapping"

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ["user", "certificate_type_display", "title", "issued_date", "verified", "created_at"]
    list_filter = ["certificate_type", "verified", "issued_date", "created_at"]
    search_fields = ["user__username", "title", "certificate_number"]
    readonly_fields = ["created_at"]
    actions = ["verify_certificates", "generate_pdfs"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'issued_by')

    def certificate_type_display(self, obj):
        type_icons = {
            'seeker_completion': '📘',
            'scholar_completion': '📖',
            'missionary_license': '🌍',
            'bible_study_leader': '👥',
            'evangelism': '🔥'
        }
        return f"{type_icons.get(obj.certificate_type, '')} {obj.get_certificate_type_display()}"
    certificate_type_display.short_description = "Certificate Type"

    def verify_certificates(self, request, queryset):
        for certificate in queryset:
            certificate.verified = True
            certificate.issued_by = request.user
            certificate.issued_date = timezone.now()
            certificate.save()
        self.message_user(request, f"Verified {queryset.count()} certificate(s).", messages.SUCCESS)
    verify_certificates.short_description = "Verify selected certificates"

    def generate_pdfs(self, request, queryset):
        # This would typically generate PDF certificates
        self.message_user(request, f"Generating PDFs for {queryset.count()} certificate(s)...", messages.INFO)
    generate_pdfs.short_description = "Generate PDF certificates"

# ===========================
# User & System Admins
# ===========================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "email_verified", "phone_number", "receive_notifications", "created_at"]
    list_filter = ["email_verified", "receive_notifications", "created_at"]
    search_fields = ["user__username", "user__email", "phone_number"]
    readonly_fields = ["created_at"]
    actions = ["verify_emails", "toggle_notifications"]

    def verify_emails(self, request, queryset):
        queryset.update(email_verified=True)
        self.message_user(request, f"Verified {queryset.count()} profile(s).", messages.SUCCESS)
    verify_emails.short_description = "Verify email addresses"

    def toggle_notifications(self, request, queryset):
        for profile in queryset:
            profile.receive_notifications = not profile.receive_notifications
            profile.save()
        self.message_user(request, f"Toggled notifications for {queryset.count()} profile(s).", messages.SUCCESS)
    toggle_notifications.short_description = "Toggle notifications"

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
    actions = ["approve_comments", "disapprove_comments"]

    def short_body(self, obj):
        return (obj.body[:80] + "…") if len(obj.body) > 80 else obj.body
    short_body.short_description = "Comment"

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"Approved {queryset.count()} comment(s).", messages.SUCCESS)
    approve_comments.short_description = "Approve selected comments"

    def disapprove_comments(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"Disapproved {queryset.count()} comment(s).", messages.SUCCESS)
    disapprove_comments.short_description = "Disapprove selected comments"

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "sent_at", "created_at", "sent_by"]
    search_fields = ["title", "body"]
    readonly_fields = ["created_at", "sent_at"]
    actions = ["send_announcements"]

    def send_announcements(self, request, queryset):
        from .utils.emailing import send_announcement_to_subscribers
        from django.contrib.auth.models import User
        
        subscribers = User.objects.filter(profile__receive_notifications=True)
        total_sent = 0
        
        for announcement in queryset:
            sent_count = send_announcement_to_subscribers(announcement, subscribers)
            total_sent += sent_count
            announcement.sent_at = timezone.now()
            announcement.sent_by = request.user
            announcement.save()
        
        self.message_user(request, f"Sent {total_sent} announcement email(s).", messages.SUCCESS)
    send_announcements.short_description = "Send selected announcements"

# ===========================
# Admin Branding
# ===========================
admin.site.site_header = "GOD CARES 365 Mission Platform"
admin.site.site_title = "GOD CARES 365 Admin"
admin.site.index_title = "Mission Dashboard"