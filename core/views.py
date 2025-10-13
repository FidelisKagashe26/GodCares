from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import NoReverseMatch
from django.db import transaction

from core.forms import ProfileForm
from content.models import Post, Lesson, Event, MediaItem, Profile  # rekebisha import zako kama path ni tofauti

# ============== SITE SEARCH ==============
def _pick_snippet(obj, fields):
    for f in fields:
        try:
            val = getattr(obj, f, "")
            if isinstance(val, str) and val.strip():
                return val
        except Exception:
            continue
    return ""

def site_search(request):
    q = (request.GET.get("q") or "").strip()
    results = []

    if q:
        # Post
        try:
            post_q = Q(title__icontains=q) | Q(content__icontains=q) | Q(excerpt__icontains=q)
            for obj in Post.pub.published().filter(post_q)[:200]:
                results.append({
                    "type": "Makala",
                    "title": obj.title,
                    "url": obj.get_absolute_url(),
                    "snippet": _pick_snippet(obj, ["excerpt", "content"]),
                })
        except Exception:
            pass

        # Lesson
        try:
            les_q = Q(title__icontains=q) | Q(description__icontains=q) | Q(content__icontains=q)
            for obj in Lesson.pub.published().filter(les_q)[:200]:
                results.append({
                    "type": "Somo",
                    "title": obj.title,
                    "url": obj.get_absolute_url(),
                    "snippet": _pick_snippet(obj, ["description", "content"]),
                })
        except Exception:
            pass

        # Event
        try:
            evt_q = Q(title__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q)
            for obj in Event.objects.filter(evt_q)[:200]:
                results.append({
                    "type": "Tukio",
                    "title": obj.title,
                    "url": obj.get_absolute_url(),
                    "snippet": _pick_snippet(obj, ["description", "location"]),
                })
        except Exception:
            pass

        # MediaItem (optional—kama hutaki, toa kipande hiki)
        try:
            mid_q = Q(title__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q)
            for obj in MediaItem.objects.filter(mid_q)[:200]:
                # kama huna page ya detail, unaweza kuacha url="" au '#'
                results.append({
                    "type": "Media",
                    "title": obj.title,
                    "url": getattr(obj, "get_absolute_url", lambda: "#")(),
                    "snippet": _pick_snippet(obj, ["description"]),
                })
        except Exception:
            pass

    paginator = Paginator(results, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    ctx = {"q": q, "total": len(results), "page_obj": page_obj}
    return render(request, "search/results.html", ctx)


# ============== ACCOUNT PROFILE ==============
@login_required
def account_profile(request):
    # hakikisha profile ipo
    Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, "Wasifu umehifadhiwa.")
            return redirect("account_profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "account/profile.html", {"form": form})
