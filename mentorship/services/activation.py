from django.conf import settings
from django.utils import timezone

def _is_email_verified(user) -> bool:
    """
    Rudisha True kama email ya mtumiaji imethibitishwa.
    Ikiwa hutumii allauth, fallback ni user.is_active (rekebisha ukihitaji).
    """
    try:
        from allauth.account.models import EmailAddress
        return EmailAddress.objects.filter(user=user, verified=True).exists()
    except Exception:
        return bool(getattr(user, "is_active", False))


def _has_completed_level1(user) -> bool:
    """
    Rudisha True kama mtumiaji amekamilisha Level 1 (kulingana na REFERRAL_LEVEL1_CODES).
    Rekebisha model/slug zako kama ilivyo kwenye mradi wako.
    """
    try:
        from progress.models import LevelProgress  # hakikisha model hii ipo kama tulivyoelekeza
        level_slugs = getattr(settings, "REFERRAL_LEVEL1_CODES", ["level-1"])
        return LevelProgress.objects.filter(
            user=user, level__slug__in=level_slugs, status="completed"
        ).exists()
    except Exception:
        return False


def is_email_verified(user) -> bool:
    """Public wrapper kwa templates/views."""
    return _is_email_verified(user)


def has_completed_level1(user) -> bool:
    """Public wrapper kwa templates/views."""
    return _has_completed_level1(user)


def try_activate_for_user(user, reason: str = "auto") -> bool:
    """
    Jaribu kui-activate referral ya user (ikiwa bado) kulingana na policy:

      REFERRAL_ACTIVATION_POLICY ∈ {"MANUAL", "AUTO_EMAIL", "AUTO_EMAIL_AND_LEVEL1", "HYBRID"}

    Kanuni:
      - AUTO_EMAIL_AND_LEVEL1: inahitaji email_verified AND level1_done
      - AUTO_EMAIL: inahitaji email_verified
      - HYBRID: inaruhusu mojawapo ya hizo mbili
      - MANUAL: haitaji chochote cha auto (admin hufanya mwenyewe)
    """
    ref = getattr(user, "referral", None)
    if not ref or ref.is_active:
        return False

    policy = str(getattr(settings, "REFERRAL_ACTIVATION_POLICY", "HYBRID")).upper()

    email_ok = _is_email_verified(user)
    level_ok = _has_completed_level1(user)

    # Kipaumbele: kama vigezo vya "email+level1" vimetimia na policy inaruhusu, tumia hicho
    if email_ok and level_ok and policy in {"AUTO_EMAIL_AND_LEVEL1", "HYBRID"}:
        ref.is_active = True
        ref.activation_method = "email+level1"
        ref.activated_at = timezone.now()
        ref.save(update_fields=["is_active", "activation_method", "activated_at"])
        return True

    # Vinginevyo, kama email_ok na policy inaruhusu email-only, tumia hicho
    if email_ok and policy in {"AUTO_EMAIL", "HYBRID"}:
        ref.is_active = True
        ref.activation_method = "email"
        ref.activated_at = timezone.now()
        ref.save(update_fields=["is_active", "activation_method", "activated_at"])
        return True

    # MANUAL au vigezo havijatimia
    return False
