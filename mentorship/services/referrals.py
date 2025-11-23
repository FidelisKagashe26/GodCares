from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from mentorship.models import Referral, Mentorship
User = get_user_model()

@transaction.atomic
def attach_referral(ref_code: str, mentee: User) -> Mentorship:
    try:
        ref = Referral.objects.select_for_update().get(code=ref_code, is_active=True)
    except Referral.DoesNotExist:
        raise ValidationError("Referral code is invalid or inactive.")

    if ref.mentor_id == mentee.id:
        raise ValidationError("You cannot refer yourself.")

    # create relation if not exists
    mentorship, created = Mentorship.objects.get_or_create(mentor=ref.mentor, mentee=mentee)
    return mentorship
