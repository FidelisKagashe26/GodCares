from django.db.models.signals import post_save, post_migrate
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib import messages
from mentorship.models import Referral, Mentorship
from mentorship.services.activation import try_activate_for_user

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_referral(sender, instance: User, created, **kwargs):
    if created and not hasattr(instance, "referral"):
        code = Referral.generate_code()
        while Referral.objects.filter(code=code).exists():
            code = Referral.generate_code()
        Referral.objects.create(mentor=instance, code=code, is_active=False)

@receiver(user_logged_in)
def auto_attach_pending_ref(sender, request, user, **kwargs):
    try_activate_for_user(user, reason="login")
    code = request.session.get("pending_ref_code")
    if not code:
        return
    try:
        ref = Referral.objects.get(code=code, is_active=True)
        if ref.mentor_id != user.id and not Mentorship.objects.filter(mentee=user).exists():
            Mentorship.objects.get_or_create(mentor=ref.mentor, mentee=user)
            messages.success(request, "Umeunganishwa na mentor aliyekualika. Karibu 😊")
        request.session.pop("pending_ref_code", None)
    except Referral.DoesNotExist:
        request.session.pop("pending_ref_code", None)

# Optional: Allauth hook
try:
    from allauth.account.signals import email_confirmed
    @receiver(email_confirmed)
    def on_email_confirmed(request, email_address, **kwargs):
        user = email_address.user
        try_activate_for_user(user, reason="email")
except Exception:
    pass

@receiver(post_migrate)
def backfill_missing_referrals(sender, **kwargs):
    app_label = getattr(sender, "label", None) or getattr(sender, "name", "")
    if "mentorship" not in str(app_label):
        return
    qs = User.objects.filter(referral__isnull=True)
    for u in qs.iterator():
        code = Referral.generate_code()
        while Referral.objects.filter(code=code).exists():
            code = Referral.generate_code()
        Referral.objects.create(mentor=u, code=code, is_active=False)
