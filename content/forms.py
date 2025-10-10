# content/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.core.validators import RegexValidator
from .models import PrayerRequest, LessonComment
import socket
try:
    import dns.resolver
    _HAS_DNSPYTHON = True
except Exception:
    _HAS_DNSPYTHON = False


def _domain_is_deliverable(domain: str, timeout: int = 3) -> bool:
    domain = (domain or "").strip().lower()
    if not domain:
        return False
    if _HAS_DNSPYTHON:
        try:
            r = dns.resolver.Resolver()
            r.lifetime = timeout
            r.timeout = timeout
            if r.resolve(domain, "MX"):
                return True
        except Exception:
            pass
    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(domain, 25)  # A/AAAA fallback
        return True
    except Exception:
        return False


class PrayerRequestForm(forms.ModelForm):
    class Meta:
        model = PrayerRequest
        fields = ['name','email','phone','category','request','is_anonymous','is_urgent']
        widgets = {
            'name': forms.TextInput(attrs={'class':'w-full px-4 py-3 border-2 border-gray-300 rounded-none','placeholder':'Jina lako kamili'}),
            'email': forms.EmailInput(attrs={'class':'w-full px-4 py-3 border-2 border-gray-300 rounded-none','placeholder':'email@example.com'}),
            'phone': forms.TextInput(attrs={'class':'w-full px-4 py-3 border-2 border-gray-300 rounded-none','placeholder':'+255 xxx xxx xxx'}),
            'category': forms.Select(attrs={'class':'w-full px-4 py-3 border-2 border-gray-300 rounded-none'}),
            'request': forms.Textarea(attrs={'class':'w-full px-4 py-3 border-2 border-gray-300 rounded-none','rows':6,'placeholder':'Andika ombi lako...'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class':'w-4 h-4'}),
            'is_urgent': forms.CheckboxInput(attrs={'class':'w-4 h-4'}),
        }
        labels = {
            'name':'Jina Lako','email':'Barua Pepe','phone':'Nambari ya Simu','category':'Aina ya Ombi',
            'request':'Ombi Lako','is_anonymous':'Tuma bila kutaja jina','is_urgent':'Ombi la haraka',
        }

    def clean(self):
        c = super().clean()
        if not c.get('is_anonymous') and not c.get('name'):
            raise forms.ValidationError('Jina ni lazima ikiwa hutaki kutuma bila kutaja jina.')
        if c.get('is_anonymous'):
            c['name']=c['email']=c['phone']=''
        return c


_phone_validator = RegexValidator(regex=r'^[0-9+\-() ]+$', message='Namba ya simu ina herufi zisizoruhusiwa.')


class SignUpForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150, required=True, label="Jina la Kwanza",
        widget=forms.TextInput(attrs={"placeholder":"Mf. Frank"})
    )
    last_name = forms.CharField(
        max_length=150, required=True, label="Jina la Mwisho",
        widget=forms.TextInput(attrs={"placeholder":"Mf. Joseph"})
    )
    password1 = forms.CharField(
        label="Nenosiri",
        widget=forms.PasswordInput(attrs={"placeholder":"Weka nenosiri","autocomplete":"new-password", "minlength":"8"})
    )
    password2 = forms.CharField(
        label="Thibitisha Nenosiri",
        widget=forms.PasswordInput(attrs={"placeholder":"Rudia nenosiri","autocomplete":"new-password", "minlength":"8"})
    )
    phone_number = forms.CharField(
        max_length=20, required=True, label="Namba ya Simu",
        validators=[_phone_validator],
        widget=forms.TextInput(attrs={"placeholder":"+255 7xx xxx xxx","autocomplete":"tel","inputmode":"tel"})
    )

    class Meta:
        model = User
        fields = ["username","first_name","last_name","email"]
        labels  = {"username":"Jina la mtumiaji","email":"Barua pepe"}
        widgets = {
            "username": forms.TextInput(attrs={"placeholder":"Mf. gc_frank","autocomplete":"username"}),
            "email": forms.EmailInput(attrs={"placeholder":"mfano@barua.com","autocomplete":"email"}),
        }

    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        base = "w-full px-4 py-3 border-2 border-gray-300 dark:border-gray-700 rounded-none bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100"
        for f in self.fields.values():
            f.widget.attrs["class"] = (f.widget.attrs.get("class","")+" "+base).strip()
        self.fields["username"].help_text = "Herufi, namba na @/./+/-/_ tu (≤150)."
        self.fields["email"].help_text    = "Tutatumia hii kuthibitisha akaunti yako."

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if get_user_model().objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Username tayari inatumika, tafadhali chagua nyingine.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Email inahitajika.")
        UserModel = get_user_model()
        if UserModel.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email tayari inatumika.")
        if getattr(settings,"STRICT_EMAIL_VALIDATION",True):
            try:
                domain = email.split("@",1)[1]
            except Exception:
                raise forms.ValidationError("Email si sahihi.")
            if not _domain_is_deliverable(domain, timeout=getattr(settings,"EMAIL_VALIDATION_TIMEOUT",3)):
                raise forms.ValidationError("Inaonekana domain ya barua pepe si halali au haipatikani (hakuna MX/A).")
        return email

    def clean(self):
        c = super().clean()
        p1, p2 = c.get("password1"), c.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2","Nenosiri halijalingana.")
        return c

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name  = self.cleaned_data["last_name"].strip()
        user.set_password(self.cleaned_data["password1"])
        # is_active itawekwa False kwenye view (double-opt-in)
        if commit:
            user.save()
            profile = getattr(user,"profile",None)
            if profile is None:
                from .models import Profile
                profile,_ = Profile.objects.get_or_create(user=user)
            profile.phone_number = self.cleaned_data["phone_number"]
            profile.save(update_fields=["phone_number"])
        return user


class LessonCommentForm(forms.ModelForm):
    class Meta:
        model = LessonComment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows":4,"placeholder":"Andika maoni yako hapa...","class":"w-full px-4 py-3 border-2 border-gray-300 rounded-none"})}
        labels  = {"body":"Maoni"}


class StrictPasswordResetForm(PasswordResetForm):
    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)
        self.fields["email"].widget.attrs.update({
            "class":"w-full px-4 py-3 border-2 border-gray-300 rounded-none",
            "placeholder":"mfano@barua.com","autocomplete":"email"
        })
    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Weka barua pepe.")
        UserModel = get_user_model()
        qs = UserModel._default_manager.filter(email__iexact=email, is_active=True)
        if getattr(settings,"RESET_REQUIRE_VERIFIED_EMAIL",False):
            qs = qs.filter(profile__email_verified=True)
        if not qs.exists():
            raise forms.ValidationError("Hakuna akaunti iliyo na barua pepe hii au haijathibitishwa.")
        return email
