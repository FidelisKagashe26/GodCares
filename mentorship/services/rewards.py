from django.db import transaction
from mentorship.models import RewardEvent, Mentorship

DEFAULT_POINTS = {
    "signup": 10,
    "level1_complete": 20,
    "baptism": 50,
    "all_levels_complete": 100,
    "becomes_mentor": 30,
}

@transaction.atomic
def award_for_mentee_event(mentee, event: str, points: int | None = None):
    """
    Mentee akipiga milestone (e.g., level1_complete/baptism), tuzo iende kwa mentor wake.
    Idempotent per (mentor, mentee, event) kutokana na unique_together.
    """
    ms = Mentorship.objects.select_related("mentor").filter(mentee=mentee).first()
    if not ms:
        return None
    mentor = ms.mentor
    pts = points if points is not None else DEFAULT_POINTS.get(event, 0)
    if pts <= 0:
        return None
    obj, created = RewardEvent.objects.get_or_create(
        mentor=mentor, mentee=mentee, event=event, defaults={"points": pts}
    )
    return obj
