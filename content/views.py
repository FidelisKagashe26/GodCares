# content/views.py
from __future__ import annotations

import datetime, re, secrets
from typing import Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import (
    HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import PrayerRequestForm, SignUpForm, LessonCommentForm
from .models import (
    Announcement, Category, Event, Lesson, LessonComment, LessonLike,
    MediaItem, Post, PrayerRequest, Profile, Season, Series
)
from .utils.emailing import send_html_email

# ------------ Settings/consts -------------
EMAIL_VERIFY_TTL = getattr(settings, "EMAIL_VERIFICATION_TIMEOUT", 60 * 30)  # 30min

# ------------ Helpers -------------

def _paginate(request: HttpRequest, qs, per_page: int = 10):
    paginator = Paginator(qs, per_page)
    return paginator.get_page(request.GET.get("page") or 1)

def _extract_youtube_id(url: str) -> Optional[str]:
    if not url:
        return None
    m = re.match(r"^https?://youtu\.be/([A-Za-z0-9_-]{6,})", url)
    if m: return m.group(1)
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", url)
    if m: return m.group(1)
    m = re.search(r"/embed/([A-Za-z0-9_-]{6,})", url)
    if m: return m.group(1)
    return None

def _referer_or(request: HttpRequest, default: str) -> str:
    return request.META.get("HTTP_REFERER") or default

def _issue_token_if_needed(profile: Profile) -> bool:
    """Toa token mpya tu kama haipo au ime-expire; rudi True kama umetengeneza mpya."""
    now = timezone.now()
    if profile.email_verification_token and profile.token_created_at:
        if now - profile.token_created_at < datetime.timedelta(seconds=EMAIL_VERIFY_TTL):
            return False
    profile.email_verification_token = secrets.token_urlsafe(32)
    profile.token_created_at = now
    profile.save(update_fields=["email_verification_token", "token_created_at"])
    return True

def _queue_verification_email(request: HttpRequest, user) -> None:
    site = get_current_site(request)
    verify_url = request.build_absolute_uri(
        reverse("content:verify_email") + f"?token={user.profile.email_verification_token}"
    )
    ctx = {
        "user": user,
        "site_name": site.name or "GOD CARES 365",
        "domain": site.domain,
        "verify_url": verify_url,
        "ttl_minutes": int(EMAIL_VERIFY_TTL / 60),
    }
    # tuma baada ya transaction ku-commit (epuka duplicates)
    transaction.on_commit(lambda: send_html_email(
        subject="Thibitisha barua pepe yako",
        to_email=user.email,
        template_name="emails/verify_email.html",
        context=ctx,
    ))

# ------------ Public pages -------------

def home(request: HttpRequest) -> HttpResponse:
    featured_posts = (
        Post.objects.filter(status="published", featured=True)
        .select_related("category", "author")
        .order_by("-published_at", "-created_at")[:3]
    )
    upcoming_events = Event.objects.filter(date__gte=timezone.now()).order_by("date")[:3]
    return render(request, "home.html", {
        "featured_posts": featured_posts,
        "upcoming_events": upcoming_events,
        "current_year": timezone.now().year,
    })

def about(request: HttpRequest) -> HttpResponse:
    return render(request, "about.html")

def news(request: HttpRequest) -> HttpResponse:
    posts = (Post.objects.filter(status="published")
             .select_related("category", "author")
             .order_by("-published_at", "-created_at"))
    categories = Category.objects.all().order_by("name")

    q = (request.GET.get("search") or "").strip()
    if q:
        posts = posts.filter(Q(title__icontains=q) | Q(content__icontains=q) | Q(excerpt__icontains=q))

    cat = (request.GET.get("category") or "").strip()
    if cat and cat != "all":
        posts = posts.filter(category__slug=cat)

    page_obj = _paginate(request, posts, per_page=6)
    return render(request, "news/list.html", {
        "page_obj": page_obj, "categories": categories, "search_query": q, "category_filter": cat,
    })

def news_detail(request: HttpRequest, slug: str) -> HttpResponse:
    post = get_object_or_404(Post.objects.select_related("category", "author"), slug=slug, status="published")
    Post.objects.filter(pk=post.pk).update(views=post.views + 1)
    post.refresh_from_db(fields=["views"])
    related_posts = (Post.objects.filter(category=post.category, status="published")
                     .exclude(pk=post.pk).order_by("-published_at", "-created_at")[:3])
    return render(request, "news/detail.html", {"post": post, "related_posts": related_posts})

def bible_studies(request: HttpRequest) -> HttpResponse:
    published_lessons_qs = Lesson.objects.filter(status="published").only("id", "slug", "title", "order", "status", "series_id")
    seasons = (Season.objects.filter(is_active=True)
               .prefetch_related(Prefetch("series__lessons", queryset=published_lessons_qs))
               .order_by("order", "-created_at"))

    lessons = (Lesson.objects.filter(status="published")
               .select_related("series", "series__season")
               .order_by("series__season__order", "series__order", "order", "-created_at"))

    q = (request.GET.get("search") or "").strip()
    if q:
        lessons = lessons.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(bible_references__icontains=q))

    s = (request.GET.get("season") or "").strip()
    if s and s != "all":
        lessons = lessons.filter(series__season__slug=s)

    lessons_page = _paginate(request, lessons, per_page=9)
    return render(request, "bible_studies/list.html", {
        "seasons": seasons, "lessons_page": lessons_page, "search_query": q, "season_filter": s,
    })

def events(request: HttpRequest) -> HttpResponse:
    all_events = Event.objects.all().order_by("date")
    now = timezone.now()
    f = (request.GET.get("filter") or "all").strip()
    if f == "upcoming":
        ev = all_events.filter(date__gte=now)
    elif f == "featured":
        ev = all_events.filter(is_featured=True)
    elif f == "past":
        ev = all_events.filter(date__lt=now)
    else:
        ev = all_events
    page_obj = _paginate(request, ev, per_page=6)
    return render(request, "events/list.html", {"page_obj": page_obj, "event_filter": f})

def event_detail(request: HttpRequest, slug: str) -> HttpResponse:
    event = get_object_or_404(Event, slug=slug)
    return render(request, "events/detail.html", {"event": event})

def prayer_requests(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PrayerRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Ombi lako limepokewa! Timu yetu itaomba kwa ajili yako.")
            return redirect("prayer_requests")
    else:
        form = PrayerRequestForm()
    return render(request, "prayer_requests.html", {"form": form})

def donations(request: HttpRequest) -> HttpResponse:
    return render(request, "donations.html")

# ------------ Lessons: detail/like/comment ------------

def lesson_detail(request: HttpRequest, slug: str) -> HttpResponse:
    lesson = get_object_or_404(Lesson.objects.select_related("series", "series__season"), slug=slug, status="published")
    Lesson.objects.filter(pk=lesson.pk).update(views=lesson.views + 1)
    lesson.refresh_from_db(fields=["views"])

    related_lessons = (Lesson.objects.filter(series=lesson.series, status="published")
                       .exclude(pk=lesson.pk).only("id", "slug", "title", "order").order_by("order")[:5])

    user_has_liked = request.user.is_authenticated and LessonLike.objects.filter(user=request.user, lesson=lesson).exists()

    comments = (lesson.lesson_comments.filter(is_approved=True).select_related("user").order_by("-created_at"))

    comment_form = LessonCommentForm()
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Tafadhali ingia kwanza ili uache maoni.")
            return redirect(f"{reverse('login')}?next={request.path}")
        key = f"last_comment_ts_{lesson.pk}"
        last = request.session.get(key)
        now_ts = int(timezone.now().timestamp())
        if last and (now_ts - int(last) < 15):
            messages.warning(request, "Umekuwa ukituma maoni haraka sana. Jaribu tena baada ya muda mfupi.")
            return redirect("content:lesson_detail", slug=slug)
        comment_form = LessonCommentForm(request.POST)
        if comment_form.is_valid():
            c = comment_form.save(commit=False)
            c.user = request.user
            c.lesson = lesson
            c.save()
            request.session[key] = now_ts
            messages.success(request, "Maoni yako yamehifadhiwa.")
            return redirect("content:lesson_detail", slug=slug)

    youtube_id = _extract_youtube_id(lesson.video_url) if lesson.video_url else None
    embed_url = f"https://www.youtube.com/embed/{youtube_id}" if youtube_id else None

    return render(request, "bible_studies/detail.html", {
        "lesson": lesson,
        "related_lessons": related_lessons,
        "user_has_liked": user_has_liked,
        "comment_form": comment_form,
        "comments": comments,
        "youtube_id": youtube_id,
        "embed_url": embed_url,
    })

@login_required
def lesson_like_toggle(request: HttpRequest, slug: str) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    lesson = get_object_or_404(Lesson, slug=slug, status="published")
    like, created = LessonLike.objects.get_or_create(user=request.user, lesson=lesson)
    if not created:
        like.delete()
        messages.info(request, "Umeondoa like yako.")
    else:
        messages.success(request, "Asante kwa kupenda somo hili!")
    return redirect("content:lesson_detail", slug=slug)

# ------------ Accounts: signup/verify/resend/subscribe/announce ------------

def signup_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = False  # subiri athibitishe email
                user.save()

                # hakikisha profile ipo kabla ya kuitumia
                profile, _ = Profile.objects.get_or_create(user=user, defaults={})
                profile.email_verified = False
                profile.save(update_fields=["email_verified"])

                if _issue_token_if_needed(profile):
                    _queue_verification_email(request, user)

            messages.success(
                request,
                f"Akaunti imeundwa. Tume-tuma kiungo cha kuthibitisha (muda wake: dakika {int(EMAIL_VERIFY_TTL/60)})."
            )
            return redirect("login")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})

def verify_email_view(request: HttpRequest) -> HttpResponse:
    token = request.GET.get("token")
    if not token:
        return HttpResponseBadRequest("Missing token.")

    with transaction.atomic():
        try:
            profile = (Profile.objects.select_for_update()
                       .select_related("user")
                       .get(email_verification_token=token))
        except Profile.DoesNotExist:
            messages.error(request, "Kiungo si sahihi au kilishatumika.")
            return redirect("login")

        # TTL
        if (not profile.token_created_at) or (
            timezone.now() - profile.token_created_at > datetime.timedelta(seconds=EMAIL_VERIFY_TTL)
        ):
            messages.error(request, "Kiungo cha uthibitisho kimeisha muda. Tafadhali omba kipya.")
            return redirect("login")

        profile.email_verified = True
        profile.email_verification_token = ""
        profile.token_created_at = None
        profile.save(update_fields=["email_verified", "email_verification_token", "token_created_at"])

        user = profile.user
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=["is_active"])

    messages.success(request, "Barua pepe imethibitishwa. Tafadhali ingia kuendelea.")
    return redirect("login")

@login_required
def resend_verification_view(request: HttpRequest) -> HttpResponse:
    profile = request.user.profile
    if profile.email_verified:
        messages.info(request, "Akaunti yako tayari imethibitishwa.")
        return redirect("home")
    with transaction.atomic():
        if _issue_token_if_needed(profile):
            _queue_verification_email(request, request.user)
    messages.success(request, "Kiungo kipya cha uthibitisho kimetumwa kwenye barua pepe yako.")
    return redirect("home")

@login_required
def subscribe_toggle(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    prof, _ = Profile.objects.get_or_create(user=request.user, defaults={"receive_notifications": True})
    prof.receive_notifications = not prof.receive_notifications
    prof.save(update_fields=["receive_notifications"])
    if prof.receive_notifications:
        messages.success(request, "Umejiunga na arifa za masomo mapya.")
    else:
        messages.info(request, "Umejiondoa kwenye arifa za masomo mapya.")
    return redirect(_referer_or(request, reverse("home")))

@login_required
def announcement_send_view(request: HttpRequest, pk: int) -> HttpResponse:
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    ann = get_object_or_404(Announcement, pk=pk)

    from django.contrib.auth.models import User
    users = User.objects.filter(profile__receive_notifications=True).select_related("profile")

    total = 0
    for u in users:
        send_html_email(
            subject=ann.title,
            to_email=u.email,
            template_name="emails/announcement.html",
            context={"user": u, "body": ann.body, "title": ann.title, "site_name": "GOD CARES 365"},
        )
        total += 1

    ann.sent_at = timezone.now()
    ann.sent_by = request.user
    ann.save(update_fields=["sent_at", "sent_by"])

    messages.success(request, f"Ujumbe umetumwa kwa waliosajiliwa kupokea taarifa ({total}).")
    return redirect("admin:index")
