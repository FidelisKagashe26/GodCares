# progress/services/tracker.py
from typing import Tuple

from django.db import transaction
from django.utils import timezone

from discipleship.models import DiscipleshipLevel, DiscipleshipLesson
from progress.models import LessonProgress, LevelProgress
from mentorship.services.rewards import award_for_mentee_event
from mentorship.services.activation import try_activate_for_user

# Aliases kwa urahisi (tunazitumia kama Level / Lesson kwenye code ya zamani)
Level = DiscipleshipLevel
Lesson = DiscipleshipLesson


@transaction.atomic
def mark_lesson_complete(user, lesson: Lesson) -> LessonProgress:
    """
    Tandika completion ya somo (idempotent), cheki kama level yote imekamilika,
    kisha cheki kama masomo yote (global) yamekamilika.

    Pia:
    - Ukimaliza Level ya order==1 kwa mara ya kwanza → tuzo 'level1_complete'
      na jaribu ku-activate referral kulingana na policy (AUTO_* / HYBRID).
    - Ukimaliza masomo yote (published) → tuzo 'all_levels_complete'.
    """
    now = timezone.now()

    # 1. Weka lesson ime-completed kwenye snapshot yetu ya progress.LessonProgress
    obj, _ = LessonProgress.objects.get_or_create(
        user=user,
        lesson=lesson,
        defaults={
            "status": "completed",
            "completed_at": now,
        },
    )

    if obj.status != "completed":
        obj.status = "completed"
        obj.completed_at = now
        obj.save(update_fields=["status", "completed_at"])

    # 2. Cheki kama level yote imekamilika kwa user huyu
    total_in_level = Lesson.objects.filter(
        level=lesson.level,
        is_published=True,
    ).count()

    done_in_level = LessonProgress.objects.filter(
        user=user,
        lesson__level=lesson.level,
        status="completed",
    ).count()

    if total_in_level and done_in_level >= total_in_level:
        lp, created = LevelProgress.objects.get_or_create(
            user=user,
            level=lesson.level,
            defaults={
                "status": "completed",
                "completed_at": now,
            },
        )

        if created:
            # Tuzo ya Level 1: mara ya kwanza tu kumaliza level yenye order==1
            if lesson.level.order == 1:
                award_for_mentee_event(user, "level1_complete")
                try_activate_for_user(user, reason="level1")

    # 3. Cheki kama amemaliza MASOMO YOTE (global, published)
    total_all = Lesson.objects.filter(is_published=True).count()
    if total_all:
        done_all = LessonProgress.objects.filter(
            user=user,
            status="completed",
        ).count()
        if done_all == total_all:
            award_for_mentee_event(user, "all_levels_complete")

    return obj


def user_level_completion_percent(user, level: Level) -> int:
    """
    Return percent ya completion ya user kwenye level fulani.
    """
    total = level.lessons.filter(is_published=True).count()
    if not total:
        return 0

    done = LessonProgress.objects.filter(
        user=user,
        lesson__level=level,
        status="completed",
    ).count()

    return int((done / total) * 100)


def user_overall_completion(user) -> Tuple[int, int, int]:
    """
    Rudisha (done, total, percent) ya masomo yote (published).
    """
    total = Lesson.objects.filter(is_published=True).count()
    if not total:
        return (0, 0, 0)

    done = LessonProgress.objects.filter(
        user=user,
        status="completed",
    ).count()

    pct = int((done / total) * 100)
    return (done, total, pct)
