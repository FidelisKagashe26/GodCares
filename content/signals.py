# content/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.conf import settings
from .models import Profile, Lesson
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import strip_tags

from .models import Post, Lesson, Event
from notifications.services import broadcast_notification
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

def _mk_url(request_path: str) -> str:
    # Ikiwa unatumia full URLs, unaweza kuibadili ijiunge na SITE_DOMAIN. Kwa sasa tunahifadhi path tu.
    return request_path

@receiver(post_save, sender=Post)
def on_post_published(sender, instance: Post, created, **kwargs):
    if instance.status == "published" and instance.published_at:
        broadcast_notification(
            title=f"Makala mpya: {instance.title}",
            body=strip_tags(instance.excerpt or instance.title),
            url=_mk_url(instance.get_absolute_url()),
            level="info",
        )

@receiver(post_save, sender=Lesson)
def on_lesson_published(sender, instance: Lesson, created, **kwargs):
    if instance.status == "published" and instance.published_at:
        broadcast_notification(
            title=f"Somo jipya: {instance.title}",
            body=strip_tags(instance.description or instance.title),
            url=_mk_url(instance.get_absolute_url()),
            level="success",
        )

@receiver(post_save, sender=Event)
def on_event_saved(sender, instance: Event, created, **kwargs):
    # Tuma arifa kila tukio jipya linaongezwa au likihaririwa (unaweza kubana kwa created tu)
    title = f"Tukio: {instance.title}"
    body = strip_tags(instance.description)[:200] if instance.description else ""
    broadcast_notification(
        title=title,
        body=body,
        url=_mk_url(instance.get_absolute_url()),
        level="info",
    )