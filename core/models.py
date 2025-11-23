# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class SystemSetting(models.Model):
    """
    System-wide settings and configuration
    """
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    data_type = models.CharField(
        max_length=20,
        choices=[
            ("string", "String"),
            ("integer", "Integer"),
            ("boolean", "Boolean"),
            ("json", "JSON"),
        ],
        default="string",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
        ordering = ["key"]

    def __str__(self):
        return f"{self.key} = {self.value}"


class UserActivity(models.Model):
    """
    Track user activities and interactions
    """
    ACTIVITY_TYPES = [
        ("login", "User Login"),
        ("logout", "User Logout"),
        ("lesson_view", "Lesson Viewed"),
        ("lesson_complete", "Lesson Completed"),
        ("mission_report", "Mission Report Created"),
        ("baptism_record", "Baptism Recorded"),
        ("prayer_request", "Prayer Request Submitted"),
        ("profile_update", "Profile Updated"),
        ("group_join", "Joined Bible Study Group"),
        ("certificate_earned", "Certificate Earned"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Activity"
        verbose_name_plural = "User Activities"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "activity_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_activity_type_display()} - {self.created_at}"


class Notification(models.Model):
    """
    System notifications for users (CORE layer).
    Kuepuka clash na app ya `notifications.Notification.recipient`,
    tunatumia related_name tofauti: `core_notifications`.
    """
    NOTIFICATION_TYPES = [
        ("system", "System Notification"),
        ("mission", "Mission Update"),
        ("lesson", "New Lesson"),
        ("event", "Event Reminder"),
        ("prayer", "Prayer Request Update"),
        ("achievement", "Achievement Unlocked"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="core_notifications",  # HAPA NDO MABADILIKO MUHIMU
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    action_url = models.URLField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=["is_read", "read_at"])


class AuditLog(models.Model):
    """
    System audit log for important actions
    """
    ACTION_TYPES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("login", "Login"),
        ("logout", "Logout"),
        ("export", "Export"),
        ("import", "Import"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action_type"]),
            models.Index(fields=["model_name", "object_id"]),
        ]

    def __str__(self):
        user_label = self.user.username if self.user else "System"
        return f"{user_label} - {self.action_type} - {self.model_name} - {self.created_at}"
