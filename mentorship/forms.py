from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from mentorship.models import Referral, Mentorship

User = get_user_model()

class AttachReferralForm(forms.Form):
    referral_code = forms.CharField(label="Referral Code", max_length=20)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_referral_code(self):
        code = self.cleaned_data["referral_code"].strip()
        try:
            ref = Referral.objects.get(code=code, is_active=True)
        except Referral.DoesNotExist:
            raise ValidationError("Referral code is invalid or inactive.")
        if ref.mentor_id == self.user.id:
            raise ValidationError("Huwezi kujirefer mwenyewe.")
        if Mentorship.objects.filter(mentee=self.user).exists():
            raise ValidationError("Tayari una mentor aliyekuhusishwa.")
        self.ref_obj = ref
        return code

    def save(self):
        ref = self.ref_obj
        ms = Mentorship.objects.create(mentor=ref.mentor, mentee=self.user)
        return ms
