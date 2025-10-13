# notifications/signals.py
from django.apps import apps
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .utils import broadcast_notification

# Tunataka Post, Lesson, Event toka app ya "content"
Post = apps.get_model("content", "Post")
Lesson = apps.get_model("content", "Lesson")
Event = apps.get_model("content", "Event")

def _was_just_published(instance, old_status):
    return (old_status != "published") and (getattr(instance, "status", None) == "published")

def _load_old(instance):
    if not instance.pk:
        return None
    Model = instance.__class__
    try:
        old = Model.objects.filter(pk=instance.pk).only("status").first()
    except Exception:
        old = None
    return getattr(old, "status", None)

@receiver(pre_save, sender=Post)
def post_pre_save(sender, instance, **kwargs):
    instance._old_status = _load_old(instance)

@receiver(pre_save, sender=Lesson)
def lesson_pre_save(sender, instance, **kwargs):
    instance._old_status = _load_old(instance)

@receiver(pre_save, sender=Event)
def event_pre_save(sender, instance, **kwargs):
    # Event haina field status, hivyo tutajulisha tu wakati wa kuundwa mara ya kwanza
    instance._is_new = instance.pk is None

@receiver(post_save, sender=Post)
def post_post_save(sender, instance, created, **kwargs):
    try:
        if created or _was_just_published(instance, getattr(instance, "_old_status", None)):
            if getattr(instance, "status", "") == "published":
                broadcast_notification(
                    title=f"Makala mpya: {instance.title}",
                    body=(instance.excerpt or "")[:300],
                    url=getattr(instance, "get_absolute_url", lambda: "#")(),
                    level="info",
                    recipients=None,      # None => all opted-in
                    send_email=True,
                    sender=None,
                )
    except Exception:
        # tusizuie save endapo kuna hitilafu ya arifa
        pass

@receiver(post_save, sender=Lesson)
def lesson_post_save(sender, instance, created, **kwargs):
    try:
        if created or _was_just_published(instance, getattr(instance, "_old_status", None)):
            if getattr(instance, "status", "") == "published":
                broadcast_notification(
                    title=f"Somo jipya: {instance.title}",
                    body=(instance.description or "")[:300],
                    url=getattr(instance, "get_absolute_url", lambda: "#")(),
                    level="success",
                    recipients=None,
                    send_email=True,
                    sender=None,
                )
    except Exception:
        pass

@receiver(post_save, sender=Event)
def event_post_save(sender, instance, created, **kwargs):
    try:
        if created:
            broadcast_notification(
                title=f"Tukio jipya: {instance.title}",
                body=(instance.description or "")[:300],
                url=getattr(instance, "get_absolute_url", lambda: "#")(),
                level="warning",
                recipients=None,
                send_email=True,
                sender=None,
            )
    except Exception:
        pass
