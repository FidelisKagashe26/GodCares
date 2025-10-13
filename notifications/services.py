# notifications/services.py
from typing import Iterable, Optional
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

from .models import Notification

User = get_user_model()

def broadcast_notification(
    *,
    title: str,
    body: str = "",
    url: str = "",
    level: str = "info",
    recipients: Optional[Iterable[User]] = None,
    sender: Optional[User] = None,
    email_subject: Optional[str] = None,
    email_from: Optional[str] = None,
) -> int:
    """
    Unda Notification kwa kila recipient. Tuma email kwa waliowasha 'receive_notifications' (kwenye Profile).
    Rudisha idadi ya waliopokea (idadi ya notifications zilizoundwa).
    """
    if recipients is None:
        recipients = User.objects.filter(is_active=True).select_related("profile")

    notifications = []
    email_list = []

    for user in recipients:
        notifications.append(Notification(
            recipient=user,
            sender=sender,
            title=title,
            body=body,
            url=url,
            level=level
        ))
        # Email kwa waliowasha tu
        prof = getattr(user, "profile", None)
        if prof and prof.receive_notifications and user.email:
            email_list.append(user.email)

    Notification.objects.bulk_create(notifications, batch_size=500)

    # Tuma email (optional)
    if email_list:
        send_mail(
            subject=email_subject or title,
            message=body or title,
            from_email=email_from or getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
            recipient_list=email_list,
            fail_silently=True,  # epuka kuvunja flow
        )

    return len(notifications)


def mark_as_read(notification: Notification):
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at"])
