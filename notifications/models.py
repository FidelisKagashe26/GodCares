# notifications/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    LEVELS = [
        ("info", "Info"),
        ("success", "Success"),
        ("warning", "Warning"),
        ("error", "Error"),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    # Hatutaonyesha jina la sender popote kwenye UI
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_notifications")

    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    url = models.URLField(blank=True)  # deeplink ya hiari
    level = models.CharField(max_length=12, choices=LEVELS, default="info")

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"[{self.level}] to {self.recipient} :: {self.title}"
