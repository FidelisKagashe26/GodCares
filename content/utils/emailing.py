# content/utils/emailing.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User

from content.models import Lesson

def send_html_email(subject: str, to_email: str, template_name: str, context: dict) -> None:
    """
    Tuma barua pepe (text + HTML). Stateless; haitoi token wala kufanya DB writes.
    """
    text_body = render_to_string(template_name.replace(".html", ".txt"), context)
    html_body = render_to_string(template_name, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        to=[to_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)

def send_welcome_email(user: User) -> None:
    ctx = {"user": user, "site_name": getattr(settings, "SITE_NAME", "GOD CARES 365")}
    send_html_email(
        subject=f"Karibu {user.get_full_name() or user.username} — {ctx['site_name']}",
        to_email=user.email,
        template_name="emails/welcome.html",
        context=ctx,
    )

def send_lesson_published_email_to_subscribers(lesson: Lesson) -> None:
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
    url = f"{site_url}/lessons/{lesson.slug}/"

    users = User.objects.filter(profile__receive_notifications=True).select_related("profile")
    # (hiari) chuja walio-thibitisha tu:
    # users = users.filter(profile__email_verified=True)

    for u in users:
        ctx = {"user": u, "lesson": lesson, "url": url, "site_name": site_name}
        send_html_email(
            subject=f"Somo Jipya: {lesson.title} — {site_name}",
            to_email=u.email,
            template_name="emails/lesson_published.html",
            context=ctx,
        )
