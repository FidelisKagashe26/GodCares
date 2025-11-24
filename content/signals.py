# backend/content/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import (
    Profile,
    DiscipleshipJourney,
    StageProgress,
    MissionReport,
    BibleStudyGroup,
    BaptismRecord,
    Certificate,
    GlobalSoulsCounter,
    Lesson,
    Post,
    LessonLike,
    LessonComment,
)


@receiver(post_save, sender=User)
def create_user_profile_and_journey(sender, instance, created, **kwargs):
    """
    Create profile and discipleship journey when a new user is created.
    """
    if created:
        Profile.objects.create(user=instance)
        DiscipleshipJourney.objects.create(user=instance)
        update_global_souls_counter()


@receiver(post_save, sender=DiscipleshipJourney)
def handle_journey_completion(sender, instance, **kwargs):
    """
    Handle actions when a user completes missionary stage.
    """
    if instance.missionary_completed and not hasattr(instance, "_certificate_created"):
        Certificate.objects.create(
            user=instance.user,
            certificate_type="missionary_license",
            title="Certified Missionary License",
            description="Awarded for completing the God Cares 365 Missionary Training Program",
            certificate_number=f"GC365-M{instance.user.id:06d}",
            issued_by=instance.user,  # practically, an admin should issue this
        )
        instance._certificate_created = True
        instance.save()
        update_global_souls_counter()


# ========== MissionReport: track verification change safely ==========

@receiver(pre_save, sender=MissionReport)
def store_verification_state(sender, instance, **kwargs):
    """
    Store old is_verified state on the instance so that post_save
    can know whether verification has just happened.
    """
    if instance.pk:
        try:
            old = MissionReport.objects.get(pk=instance.pk)
            instance._was_verified = old.is_verified
        except MissionReport.DoesNotExist:
            instance._was_verified = False
    else:
        instance._was_verified = False


@receiver(post_save, sender=MissionReport)
def update_souls_counter_on_mission(sender, instance, created, **kwargs):
    """
    Update global souls counter *only* when a mission report transitions
    from unverified -> verified.
    """
    was_verified = getattr(instance, "_was_verified", False)
    if not was_verified and instance.is_verified:
        global_counter, _ = GlobalSoulsCounter.objects.get_or_create(pk=1)
        global_counter.total_souls_reached += instance.souls_reached
        global_counter.total_baptisms += instance.baptisms_performed
        global_counter.total_mission_reports += 1
        global_counter.save()


@receiver(post_save, sender=BaptismRecord)
def update_baptism_counter(sender, instance, created, **kwargs):
    """
    Update baptism count when a new baptism record is created.
    """
    if created:
        global_counter, _ = GlobalSoulsCounter.objects.get_or_create(pk=1)
        global_counter.total_baptisms += 1
        global_counter.save()


@receiver(post_save, sender=BibleStudyGroup)
def update_groups_counter(sender, instance, created, **kwargs):
    """
    Update Bible study groups counter when a new active group is created.
    """
    if created and instance.is_active:
        global_counter, _ = GlobalSoulsCounter.objects.get_or_create(pk=1)
        global_counter.total_bible_study_groups += 1
        global_counter.save()


@receiver(post_save, sender=Lesson)
def create_stage_progress_for_published_lessons(sender, instance, created, **kwargs):
    """
    Placeholder: hapa unaweza ku-generate StageProgress zako
    ukitaka ziji-create auto kwa watumiaji.
    """
    if instance.status == "published" and instance.published_at:
        # TODO: logic ya auto-assign lessons to journeys/stages kama itahitajika
        pass


@receiver(post_save, sender=StageProgress)
def update_journey_progress(sender, instance, **kwargs):
    """
    Update overall journey progress when stage progress is updated.
    """
    if instance.completed:
        journey = instance.journey

        total_lessons_in_stage = StageProgress.objects.filter(
            journey=journey, stage=journey.current_stage
        ).count()

        completed_lessons_in_stage = StageProgress.objects.filter(
            journey=journey, stage=journey.current_stage, completed=True
        ).count()

        if total_lessons_in_stage > 0:
            stage_progress = (completed_lessons_in_stage / total_lessons_in_stage) * 100
            journey.progress_percentage = int(stage_progress)

            if completed_lessons_in_stage == total_lessons_in_stage:
                if journey.current_stage == "seeker":
                    journey.seeker_completed = True
                elif journey.current_stage == "scholar":
                    journey.scholar_completed = True

            journey.save()


@receiver(pre_save, sender=User)
def update_active_missionaries_count(sender, instance, **kwargs):
    """
    Update active missionaries count when user status changes.
    """
    if instance.pk:
        try:
            old_user = User.objects.get(pk=instance.pk)
            if old_user.is_active != instance.is_active:
                update_global_souls_counter()
        except User.DoesNotExist:
            pass


def update_global_souls_counter():
    """
    Update derived counts in the global souls counter.
    """
    global_counter, _ = GlobalSoulsCounter.objects.get_or_create(pk=1)

    active_missionaries = DiscipleshipJourney.objects.filter(
        missionary_completed=True
    ).count()

    active_groups = BibleStudyGroup.objects.filter(is_active=True).count()

    global_counter.active_missionaries = active_missionaries
    global_counter.total_bible_study_groups = active_groups
    global_counter.save()

@receiver(post_save, sender=GlobalSoulsCounter)
def initialize_global_counter(sender, instance, created, **kwargs):
    if created:
        update_global_souls_counter()
