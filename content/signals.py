# content/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from .models import Profile, Lesson
from .utils.emailing import (
    send_welcome_email,
    send_verification_email,
    send_lesson_published_email_to_subscribers,
)

@receiver(post_save, sender=User)
def create_profile_and_send_emails(sender, instance, created, **kwargs):
    if created:
        profile = Profile.objects.create(user=instance)
        # welcome + verification
        send_welcome_email(instance)
        send_verification_email(instance)

@receiver(post_save, sender=Lesson)
def lesson_publish_notifier(sender, instance: Lesson, created, **kwargs):
    # Notify only when published and has published_at set
    if instance.status == 'published' and instance.published_at:
        # send to subscribers (verified OR not? hapa tumetumia receive_notifications tu)
        send_lesson_published_email_to_subscribers(instance)

@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance, defaults={"receive_notifications": True})
    else:
        Profile.objects.get_or_create(user=instance)