from django.db import models
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

User = get_user_model()

class Referral(models.Model):
    mentor = models.OneToOneField(User, related_name="referral", on_delete=models.CASCADE)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    is_active = models.BooleanField(default=False)
    activation_method = models.CharField(
        max_length=24,
        choices=[("manual","manual"),("email","email"),("email+level1","email+level1")],
        null=True, blank=True,
    )
    activated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_code(prefix="GC365-"):
        token = get_random_string(6).upper()
        return f"{prefix}{token}"

    def __str__(self):
        return f"{self.mentor} → {self.code}"


class Mentorship(models.Model):
    mentor = models.ForeignKey(User, related_name="my_mentees", on_delete=models.CASCADE)
    mentee = models.ForeignKey(User, related_name="my_mentor_link", on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        # mentee awe na mentor mmoja tu
        constraints = [
            models.UniqueConstraint(fields=["mentee"], name="unique_single_mentor_per_mentee"),
        ]

    def __str__(self):
        return f"{self.mentor} ↔ {self.mentee}"


class RewardEvent(models.Model):
    EVENT_CHOICES = [
        ("signup", "Signup via referral"),
        ("level1_complete", "Level 1 completed"),
        ("baptism", "Baptism"),
        ("all_levels_complete", "All levels completed"),
        ("becomes_mentor", "Mentee becomes mentor"),
    ]
    mentor = models.ForeignKey(User, related_name="reward_events", on_delete=models.CASCADE)
    mentee = models.ForeignKey(User, null=True, blank=True, related_name="reward_source", on_delete=models.SET_NULL)
    event = models.CharField(max_length=32, choices=EVENT_CHOICES)
    points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["mentor", "event", "created_at"])]
        unique_together = (("mentor", "mentee", "event"),)

    def __str__(self):
        who = f"{self.mentor}"
        if self.mentee:
            who += f" ← {self.mentee}"
        return f"{who} [{self.event}] +{self.points}pts"
