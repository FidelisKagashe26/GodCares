# content/utils/emailing.py
from __future__ import annotations

import logging
from typing import Iterable, Optional
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser

from content.models import Lesson, MissionReport, DiscipleshipJourney, Certificate

logger = logging.getLogger(__name__)
UserModel = get_user_model()

def _render_email_bodies(template_name: str, context: dict) -> tuple[str, str]:
    """
    Tengeneza (text_body, html_body).
    """
    html_body = render_to_string(template_name, context)

    text_tpl = template_name.replace(".html", ".txt")
    try:
        text_body = render_to_string(text_tpl, context)
    except TemplateDoesNotExist:
        text_body = strip_tags(html_body)

    return text_body, html_body

def _get_from_email() -> str:
    return getattr(settings, "DEFAULT_FROM_EMAIL", "GOD CARES 365 <no-reply@localhost>")

def send_html_email(
    subject: str,
    to_email: str,
    template_name: str,
    context: dict,
    *,
    reply_to: Optional[Iterable[str]] = None,
    bcc: Optional[Iterable[str]] = None,
) -> bool:
    """
    Tuma barua pepe (text + HTML).
    """
    text_body, html_body = _render_email_bodies(template_name, context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=_get_from_email(),
        to=[to_email],
        bcc=list(bcc) if bcc else None,
        reply_to=list(reply_to) if reply_to else None,
    )
    msg.attach_alternative(html_body, "text/html")

    fail_silently = getattr(settings, "EMAIL_FAIL_SILENTLY", settings.DEBUG)

    try:
        sent = msg.send(fail_silently=fail_silently)
        return bool(sent)
    except Exception as e:
        logger.exception("Email send failed (to=%s, subject=%s): %s", to_email, subject, e)
        return False

# ==================== MISSION PLATFORM EMAILS ====================

def send_welcome_email(user: AbstractBaseUser) -> bool:
    """
    Tuma barua pepe ya 'Karibu' kwa Mission Platform.
    """
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
    
    display_name = getattr(user, "get_full_name", lambda: "")() or getattr(user, "get_username", lambda: "")()
    
    ctx = {
        "user": user,
        "site_name": site_name,
        "site_url": site_url,
        "display_name": display_name
    }
    
    return send_html_email(
        subject=f"🌍 Karibu {display_name} - God Cares 365 Mission Platform",
        to_email=user.email,
        template_name="emails/welcome.html",
        context=ctx,
    )

def send_verification_email(user: AbstractBaseUser, verification_url: str) -> bool:
    """
    Tuma barua pepe ya uthibitishaji.
    """
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    display_name = getattr(user, "get_full_name", lambda: "")() or getattr(user, "get_username", lambda: "")()
    
    ctx = {
        "user": user,
        "site_name": site_name,
        "verification_url": verification_url,
        "display_name": display_name
    }
    
    return send_html_email(
        subject=f"✅ Thibitisha Barua Pepe Yako - God Cares 365",
        to_email=user.email,
        template_name="emails/verify_email.html",
        context=ctx,
    )

def send_stage_completion_email(user: AbstractBaseUser, stage: str, certificate_url: str = None) -> bool:
    """
    Tuma barua pepe wakati user anamaliza stage ya discipleship.
    """
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    
    stage_titles = {
        'seeker': '📘 Discover Truth - God Cares 365 Student',
        'scholar': '📖 Understand Prophecy - God Cares 365 Prophecy Student',
        'missionary': '🌍 Live & Share Message - God Cares 365 Missionary'
    }
    
    ctx = {
        "user": user,
        "site_name": site_name,
        "stage": stage,
        "stage_title": stage_titles.get(stage, stage),
        "certificate_url": certificate_url
    }
    
    return send_html_email(
        subject=f"🎓 Umemaliza {stage_titles.get(stage, stage)}!",
        to_email=user.email,
        template_name="emails/stage_completion.html",
        context=ctx,
    )

def send_mission_accomplished_email(mission_report: MissionReport) -> bool:
    """
    Tuma barua pepe wakati mission report inakubaliwa.
    """
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    
    ctx = {
        "user": mission_report.missionary,
        "site_name": site_name,
        "mission_report": mission_report,
        "souls_reached": mission_report.souls_reached,
        "baptisms_performed": mission_report.baptisms_performed
    }
    
    return send_html_email(
        subject=f"✅ Mission Report Imethibitishwa - {mission_report.title}",
        to_email=mission_report.missionary.email,
        template_name="emails/mission_accomplished.html",
        context=ctx,
    )

def send_certificate_issued_email(certificate: Certificate) -> bool:
    """
    Tuma barua pepe wakati certificate inatolewa.
    """
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    
    ctx = {
        "user": certificate.user,
        "site_name": site_name,
        "certificate": certificate,
        "certificate_url": f"/api/certificates/{certificate.id}/download/"  # Adjust as needed
    }
    
    return send_html_email(
        subject=f"🏆 Umepata Cheti - {certificate.title}",
        to_email=certificate.user.email,
        template_name="emails/certificate_issued.html",
        context=ctx,
    )

def send_bible_study_group_invite(group, invited_user, invite_url: str) -> bool:
    """
    Tuma barua pepe ya kukaribisha kwenye Bible study group.
    """
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    
    ctx = {
        "user": invited_user,
        "site_name": site_name,
        "group": group,
        "invite_url": invite_url,
        "leader_name": group.leader.get_full_name() or group.leader.username
    }
    
    return send_html_email(
        subject=f"👥 Umealikwa Kwenye Kikundi cha Biblia - {group.group_name}",
        to_email=invited_user.email,
        template_name="emails/group_invite.html",
        context=ctx,
    )

def send_global_mission_update(users: Iterable[AbstractBaseUser], stats: dict) -> int:
    """
    Tuma barua pepe ya updates za global mission kwa wote.
    """
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    total_sent = 0
    
    for user in users:
        ctx = {
            "user": user,
            "site_name": site_name,
            "stats": stats
        }
        
        success = send_html_email(
            subject=f"🌍 Global Mission Update - {stats.get('total_souls_reached', 0)} Souls Reached!",
            to_email=user.email,
            template_name="emails/global_update.html",
            context=ctx,
        )
        
        if success:
            total_sent += 1
    
    return total_sent

def send_prayer_request_notification(prayer_request, admin_users: Iterable[AbstractBaseUser]) -> int:
    """
    Tuma barua pepe kwa admins wakati prayer request mpya inapokewa.
    """
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    total_sent = 0
    
    for admin_user in admin_users:
        ctx = {
            "user": admin_user,
            "site_name": site_name,
            "prayer_request": prayer_request,
            "is_anonymous": prayer_request.is_anonymous
        }
        
        success = send_html_email(
            subject=f"🙏 Ombi Jipya la Maombi - {prayer_request.get_category_display()}",
            to_email=admin_user.email,
            template_name="emails/prayer_request_notification.html",
            context=ctx,
        )
        
        if success:
            total_sent += 1
    
    return total_sent

# ==================== BULK EMAIL FUNCTIONS ====================

def send_bulk_missionary_update(missionaries: Iterable[AbstractBaseUser], update_data: dict) -> int:
    """
    Tuma barua pepe ya update kwa missionaries wote.
    """
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    total_sent = 0
    
    # Use single connection for better performance
    fail_silently = getattr(settings, "EMAIL_FAIL_SILENTLY", settings.DEBUG)
    connection = get_connection(fail_silently=fail_silently)
    
    try:
        connection.open()
    except Exception as e:
        logger.exception("Failed to open email connection: %s", e)
        if fail_silently:
            return 0
        raise
    
    try:
        for missionary in missionaries:
            ctx = {
                "user": missionary,
                "site_name": site_name,
                "update_data": update_data
            }
            
            text_body, html_body = _render_email_bodies("emails/missionary_update.html", ctx)
            
            msg = EmailMultiAlternatives(
                subject=f"🌍 Mission Update - {site_name}",
                body=text_body,
                from_email=_get_from_email(),
                to=[missionary.email],
                connection=connection,
            )
            msg.attach_alternative(html_body, "text/html")
            
            try:
                sent = msg.send(fail_silently=fail_silently)
                total_sent += int(bool(sent))
            except Exception as e:
                logger.warning("Could not send missionary update to %s: %s", missionary.email, e)
                if not fail_silently:
                    raise
    finally:
        try:
            connection.close()
        except Exception:
            pass
    
    return total_sent

def send_announcement_to_subscribers(announcement, subscribers: Iterable[AbstractBaseUser]) -> int:
    """
    Tuma announcement kwa wote waliowasha notifications.
    """
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    total_sent = 0
    
    fail_silently = getattr(settings, "EMAIL_FAIL_SILENTLY", settings.DEBUG)
    connection = get_connection(fail_silently=fail_silently)
    
    try:
        connection.open()
    except Exception as e:
        logger.exception("Failed to open email connection: %s", e)
        if fail_silently:
            return 0
        raise
    
    try:
        for subscriber in subscribers:
            ctx = {
                "user": subscriber,
                "site_name": site_name,
                "announcement": announcement
            }
            
            text_body, html_body = _render_email_bodies("emails/announcement.html", ctx)
            
            msg = EmailMultiAlternatives(
                subject=f"📢 {announcement.title} - {site_name}",
                body=text_body,
                from_email=_get_from_email(),
                to=[subscriber.email],
                connection=connection,
            )
            msg.attach_alternative(html_body, "text/html")
            
            try:
                sent = msg.send(fail_silently=fail_silently)
                total_sent += int(bool(sent))
            except Exception as e:
                logger.warning("Could not send announcement to %s: %s", subscriber.email, e)
                if not fail_silently:
                    raise
    finally:
        try:
            connection.close()
        except Exception:
            pass
    
    return total_sent

# ==================== LEGACY FUNCTIONS (FOR COMPATIBILITY) ====================

def send_lesson_published_email_to_subscribers(lesson: Lesson) -> int:
    """
    Legacy function - Tuma barua pepe kuhusu somo jipya kwa subscribers.
    """
    from django.contrib.auth.models import User
    
    subscribers = User.objects.filter(
        profile__receive_notifications=True
    ).select_related("profile")
    
    site_name = getattr(settings, "SITE_NAME", "GOD CARES 365")
    site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
    url = f"{site_url}/api/lessons/{lesson.id}/"
    
    total_sent = 0
    
    for subscriber in subscribers:
        ctx = {
            "user": subscriber,
            "lesson": lesson,
            "url": url,
            "site_name": site_name,
        }
        
        success = send_html_email(
            subject=f"📚 Somo Jipya: {lesson.title} — {site_name}",
            to_email=subscriber.email,
            template_name="emails/lesson_published.html",
            context=ctx,
        )
        
        if success:
            total_sent += 1
    
    return total_sent