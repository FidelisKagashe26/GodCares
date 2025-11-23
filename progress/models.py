# progress/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from discipleship.models import DiscipleshipLevel, DiscipleshipLesson

User = get_user_model()


class LessonProgress(models.Model):
    """
    Snapshot ya safari ya mtumiaji kwenye kila DiscipleshipLesson.

    Inatumika kwa:
    - My Progress (dashboard ya user)
    - Mentee Progress (mentor akimuangalia mentee)
    - Global analytics (kuhesabu masomo yaliyokamilishwa n.k.)
    """

    STATUS = (
        ("not_started", "Not started"),
        ("in_progress", "In progress"),
        ("completed", "Completed"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lesson_progress_entries",
    )
    lesson = models.ForeignKey(
        DiscipleshipLesson,
        on_delete=models.CASCADE,
        related_name="user_progress_entries",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="not_started",
    )
    score = models.IntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lesson Progress"
        verbose_name_plural = "Lesson Progress"
        unique_together = (("user", "lesson"),)
        indexes = [
            models.Index(fields=["user", "lesson"]),
            models.Index(fields=["user", "status"]),
        ]
        ordering = ["-completed_at", "-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} - {self.status}"


class LevelProgress(models.Model):
    """
    Snapshot ya completion ya DiscipleshipLevel kwa kila user.

    Hii inasaidia:
    - Progress bar ya kila level (Seeker / Scholar / Missionary)
    - Ripoti za 'how many users finished this level'
    """

    STATUS = (("completed", "Completed"),)

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="level_progress_entries",
    )
    level = models.ForeignKey(
        DiscipleshipLevel,
        on_delete=models.CASCADE,
        related_name="user_progress_entries",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="completed",
    )
    completed_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Level Progress"
        verbose_name_plural = "Level Progress"
        unique_together = (("user", "level"),)
        indexes = [
            models.Index(fields=["user", "level"]),
        ]
        ordering = ["-completed_at", "-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.level.path.name} / {self.level.name} - {self.status}"
