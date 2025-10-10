# content/utils/emailing.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.contrib.auth.models import User

from content.models import Profile, Lesson

def _send_html_email(subject, to_email, template_name, context):
    html = render_to_string(template_name, context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=html,  # fallback text = html (bado itaingia)
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
        to=[to_email],
    )
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=True)

def send_welcome_email(user: User):
    ctx = {"user": user, "site_name": getattr(settings, "SITE_NAME", "GOD CARES 365")}
    _send_html_email(
        subject=f"Karibu {user.username} — {ctx['site_name']}",
        to_email=user.email,
        template_name="emails/welcome.html",
        context=ctx,
    )

def send_verification_email(user: User):
    profile = user.profile
    token = get_random_string(48)
    profile.email_verification_token = token
    profile.token_created_at = timezone.now()
    profile.save()

    verify_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/verify-email/?token={token}"
    ctx = {"user": user, "verify_url": verify_url, "site_name": getattr(settings, "SITE_NAME", "GOD CARES 365")}
    _send_html_email(
        subject="Thibitisha barua pepe yako",
        to_email=user.email,
        template_name="emails/verify_email.html",
        context=ctx,
    )

def send_lesson_published_email_to_subscribers(lesson: Lesson):
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
    url = f"{site_url}/lessons/{lesson.slug}/"
    users = User.objects.filter(profile__receive_notifications=True).select_related("profile")
    # Optional filter: only verified
    # users = users.filter(profile__email_verified=True)

    for u in users:
        ctx = {"user": u, "lesson": lesson, "url": url, "site_name": site_name}
        _send_html_email(
            subject=f"Somo Jipya: {lesson.title} — {site_name}",
            to_email=u.email,
            template_name="emails/lesson_published.html",
            context=ctx,
        )
