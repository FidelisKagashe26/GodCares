# core/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class ReferralCodeCaptureMiddleware(MiddlewareMixin):
    """
    Capture referral codes from URL parameters and store them in the session.
    """

    def process_request(self, request):
        ref = request.GET.get("ref")
        if ref:
            request.session["pending_ref_code"] = ref
            logger.info("Referral code captured: %s", ref)


class MissionTrackingMiddleware(MiddlewareMixin):
    """
    Lightweight middleware to update basic mission-related tracking for
    authenticated users (e.g. last active timestamp on the profile if present).
    """

    def process_request(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return

        # Update last_active on Profile *only if* the field exists
        try:
            profile = user.profile
        except Exception:
            return

        now = timezone.now()
        if hasattr(profile, "last_active"):
            profile.last_active = now
            try:
                profile.save(update_fields=["last_active"])
            except Exception as exc:
                logger.warning(
                    "Failed to update profile.last_active for %s: %s",
                    user.username,
                    exc,
                )


class DiscipleshipJourneyMiddleware(MiddlewareMixin):
    """
    Ensure every authenticated user has a DiscipleshipJourney record.
    This complements the signal-based creation and acts as a safety net.
    """

    def process_response(self, request, response):
        user = getattr(request, "user", None)
        if (
            not user
            or not user.is_authenticated
            or getattr(request, "_journey_checked", False)
            or response.status_code not in (200, 302)
        ):
            return response

        try:
            from content.models import DiscipleshipJourney

            journey, created = DiscipleshipJourney.objects.get_or_create(user=user)
            if created:
                logger.info(
                    "Created discipleship journey for user: %s",
                    user.username,
                )
            request._journey_checked = True
        except Exception as exc:
            logger.error(
                "Failed to ensure discipleship journey for %s: %s",
                user.username,
                exc,
            )

        return response
