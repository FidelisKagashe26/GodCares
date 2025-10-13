# notifications/utils.py
from typing import Iterable, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mass_mail
from django.db import transaction
from django.template.loader import render_to_string

from .models import Notification

User = get_user_model()

def _from_email():
    # Jaribu kupata jina la kirafiki
    name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
    return f"{name} <{email}>"

def _opted_in_users() -> Iterable[User]:
    # Users walio hai + profile.receive_notifications True
    qs = (
        User.objects.filter(is_active=True, profile__receive_notifications=True)
        .select_related("profile")
        .only("id", "email", "username", "first_name", "last_name")
    )
    return qs

@transaction.atomic
def broadcast_notification(
    *,
    title: str,
    body: str = "",
    url: str = "",
    level: str = "info",
    recipients: Optional[Iterable[User]] = None,  # None => all opted-in
    send_email: bool = True,
    sender: Optional[User] = None,
) -> int:
    """
    Tengeneza Notification records (moja kwa kila mpokeaji).
    Ikiwa send_email=True, tuma pia barua pepe kwa walio na email + wamewasha.
    Hatumtaji mtumaji kwa hadhara; 'sender' inahifadhiwa tu kwenye record kwa audit.
    """
    if recipients is None:
        recipients = list(_opted_in_users())
    else:
        recipients = list(recipients)

    notifs = []
    emails = []
    from_email = _from_email()

    for u in recipients:
        n = Notification(
            recipient=u,
            sender=sender,
            title=title,
            body=body or "",
            url=url or "",
            level=level,
        )
        notifs.append(n)

        if send_email and getattr(u, "profile", None) and getattr(u.profile, "receive_notifications", False):
            if u.email:
                # Email ya kawaida, unaweza customize template
                subject = title
                # Unaweza kutengeneza template yako ya email (HTML/text)
                message = render_to_string(
                    "emails/notification.txt",
                    {"user": u, "title": title, "body": body, "url": url, "site_name": getattr(settings, "SITE_NAME", "GOD CARES 365")}
                )
                emails.append((subject, message, from_email, [u.email]))

    if notifs:
        Notification.objects.bulk_create(notifs, batch_size=500)

    if emails:
        # Kwenye dev unaweza kuweka EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
        send_mass_mail(emails, fail_silently=True)

    return len(notifs)
