import re
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm

User = get_user_model()

_TW_INPUT = (
    "w-full border-2 border-gray-300 dark:border-gray-700 "
    "bg-white dark:bg-gray-900 text-gray-900 dark:text-white "
    "rounded-none px-3 py-2 focus:outline-none focus:ring-0 "
    "focus:border-[var(--accent-600)]"
)

class CustomPasswordChangeForm(DjangoPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs.update({"class": _TW_INPUT, "autocomplete": "current-password"})
        self.fields["new_password1"].widget.attrs.update({"class": _TW_INPUT, "autocomplete": "new-password"})
        self.fields["new_password2"].widget.attrs.update({"class": _TW_INPUT, "autocomplete": "new-password"})


class ProfileForm(forms.ModelForm):
    phone_number = forms.CharField(required=False, label="Namba ya Simu")
    receive_notifications = forms.BooleanField(required=False, label="Pokea arifa kwenye email")

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
        widgets = {
            "username":   forms.TextInput(attrs={"class": _TW_INPUT, "autocomplete": "username"}),
            "first_name": forms.TextInput(attrs={"class": _TW_INPUT, "autocomplete": "given-name"}),
            "last_name":  forms.TextInput(attrs={"class": _TW_INPUT, "autocomplete": "family-name"}),
            "email":      forms.EmailInput(attrs={"class": _TW_INPUT, "autocomplete": "email"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Maingiliano ya Profile
        user = self.instance
        prof = getattr(user, "profile", None)
        if prof:
            self.fields["phone_number"].initial = prof.phone_number or ""
            self.fields["receive_notifications"].initial = bool(prof.receive_notifications)

        # weka classes kwa extra fields
        self.fields["phone_number"].widget.attrs.update({"class": _TW_INPUT, "autocomplete": "tel"})
        self.fields["receive_notifications"].widget.attrs.update({"class": "h-4 w-4"})

    def clean_username(self):
        uname = (self.cleaned_data.get("username") or "").strip()
        if not uname:
            raise ValidationError("Username haiwezi kuwa tupu.")
        if User.objects.exclude(pk=self.instance.pk).filter(username__iexact=uname).exists():
            raise ValidationError("Username tayari imetumika.")
        return uname

    def clean_phone_number(self):
        v = (self.cleaned_data.get("phone_number") or "").strip()
        if v and not re.match(r'^[0-9+\-() ]+$', v):
            raise ValidationError("Namba ya simu si sahihi (ruhusiwa: 0-9, + - ( ) na nafasi).")
        return v

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Hakikisha profile ipo
        prof = getattr(user, "profile", None)
        if prof is None:
            from content.models import Profile  # adjust kama path ni tofauti
            prof, _ = Profile.objects.get_or_create(user=user)

        prof.phone_number = self.cleaned_data.get("phone_number", "") or ""
        prof.receive_notifications = bool(self.cleaned_data.get("receive_notifications"))

        if commit:
            prof.save(update_fields=["phone_number", "receive_notifications"])
        else:
            # kama hutaki commit mara moja, rudisha user na prof kwa caller a-deal
            pass

        return user
