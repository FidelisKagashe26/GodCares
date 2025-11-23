from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse, NoReverseMatch
from django.utils import timezone
from django.views.generic import TemplateView, ListView

from mentorship.models import Mentorship, RewardEvent, Referral
from mentorship.forms import AttachReferralForm
from mentorship.services.activation import is_email_verified, has_completed_level1

from discipleship.models import Level, Lesson  # kwa link ya kuanza Level 1 haraka


# --- Helper: hakikisha kila mtumiaji ana Referral (ikiikosa, tengeneza inactive) ---
def ensure_referral_for(user) -> Referral:
    try:
        return user.referral
    except Referral.DoesNotExist:
        code = Referral.generate_code()
        while Referral.objects.filter(code=code).exists():
            code = Referral.generate_code()
        return Referral.objects.create(mentor=user, code=code, is_active=False)


class MyReferralView(LoginRequiredMixin, TemplateView):
    template_name = "mentorship/referral.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Hakikisha kuna Referral daima
        ref = ensure_referral_for(self.request.user)
        ctx["referral"] = ref

        # Pending referral kutoka kwenye link ya mwaliko
        ctx["pending_ref_code"] = self.request.session.get("pending_ref_code")

        # Absolute invite URL (short-link): /mentorship/r/<CODE>/
        ref_path = reverse("mentorship:ref_redirect", args=[ref.code])
        ctx["invite_url"] = self.request.build_absolute_uri(ref_path)

        # Activation hints kwa UX bora
        ctx["activation"] = {
            "policy": getattr(settings, "REFERRAL_ACTIVATION_POLICY", "HYBRID"),
            "email_verified": is_email_verified(self.request.user),
            "level1_done": has_completed_level1(self.request.user),
        }

        # (Optional) Onyesha link ya kuanza Level 1 kwa haraka
        lvl1 = Level.objects.filter(is_active=True).order_by("order").first()
        first = None
        if lvl1:
            first = Lesson.objects.filter(level=lvl1, is_published=True).order_by("order").first()
        if lvl1 and first:
            ctx["level1_url"] = self.request.build_absolute_uri(
                reverse("discipleship:lesson", args=[lvl1.slug, first.slug])
            )

        # (Optional) Allauth 'account_email' URL – weka tu ikiwa ipo ili template isivunjike
        try:
            ctx["account_email_url"] = reverse("account_email")
        except NoReverseMatch:
            ctx["account_email_url"] = None

        return ctx


# --- Helper: reverse ya kwanza itakayopatikana kati ya majina kadhaa ---
def _reverse_first(names):
    for n in names:
        if not n:
            continue
        try:
            return reverse(n)
        except NoReverseMatch:
            continue
    return None


def referral_redirect(request, code: str):
    """
    Link fupi: /mentorship/r/<CODE>/
    - Hifadhi code kwenye session
    - Kama user amelogin → mpeleke ku-attach sasa
    - Kama si login → mpeleke signup/login akirudi aende attach, huku tukibeba ?next= na ?ref=
    """
    request.session["pending_ref_code"] = code

    if request.user.is_authenticated:
        return redirect("mentorship:attach_referral")

    # next target baada ya auth
    next_url = reverse("mentorship:attach_referral")

    # Jaribu majina ya kawaida ya signup/login
    candidates = [
        getattr(settings, "MENTORSHIP_SIGNUP_URL_NAME", None),  # preference kutoka settings
        "content:signup",          # kama unavyoitumia kwenye templates
        "account_signup",          # django-allauth
        "signup", "register",      # majina ya kawaida
        "login", "account_login",  # fallback kwenda login
        "content:login",
    ]

    base = _reverse_first(candidates)
    if base:
        qs = urlencode({"next": next_url, "ref": code})
        return redirect(f"{base}?{qs}")

    # Mwisho kabisa: nenda nyumbani
    return redirect("/")


@login_required
def attach_referral_view(request):
    """
    Fomu ya kuunganisha referral kwa user aliyelogin.
    Ina rate-limit ndogo kupitia session ili kuzuia kubahatisha code mara nyingi.
    """
    now = timezone.now().timestamp()
    window = 10 * 60  # dakika 10
    max_attempts = 5
    key = "attach_attempts"

    # Dumisha attempts zilizopo tu kwenye dirisha la muda
    bucket = [t for t in request.session.get(key, []) if now - t < window]

    # Jaza awali kutoka session (kama ametoka kwenye short-link)
    initial = {}
    pref = request.session.get("pending_ref_code")
    if pref:
        initial["referral_code"] = pref

    if request.method == "POST":
        if len(bucket) >= max_attempts:
            messages.error(request, "Umefanya majaribio mengi. Jaribu tena baadae kidogo.")
            return redirect("mentorship:attach_referral")

        form = AttachReferralForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Umefanikiwa ku-attach referral code. Karibu kwenye safari ya ukuaji! 🙌")
            # Safisha session state
            request.session.pop("pending_ref_code", None)
            request.session.pop(key, None)
            return redirect("mentorship:my_referral")
        else:
            bucket.append(now)
            request.session[key] = bucket
    else:
        form = AttachReferralForm(initial=initial, user=request.user)

    return render(request, "mentorship/attach_referral.html", {"form": form})


class MyMenteesView(LoginRequiredMixin, ListView):
    template_name = "mentorship/mentor_dashboard.html"
    context_object_name = "mentees"

    def get_queryset(self):
        return (
            Mentorship.objects
            .select_related("mentee")
            .filter(mentor=self.request.user)
            .order_by("-date_joined")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        total_points = RewardEvent.objects.filter(mentor=self.request.user).aggregate(s=Sum("points"))["s"] or 0
        ctx["total_points"] = total_points
        return ctx


class LeaderboardView(LoginRequiredMixin, ListView):
    template_name = "mentorship/leaderboard.html"
    context_object_name = "leaders"

    def get_queryset(self):
        return (
            RewardEvent.objects
            .values("mentor__id", "mentor__username")
            .annotate(points=Sum("points"))
            .order_by("-points")
        )[:50]
