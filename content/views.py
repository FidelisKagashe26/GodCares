from __future__ import annotations

from typing import Any, Optional, Tuple
import re

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, Page
from django.db import transaction
from django.db.models import Q, Count, Prefetch
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import PrayerRequestForm, SignUpForm, LessonCommentForm
from .models import (
    Announcement,
    Category,
    Event,
    Lesson,
    LessonComment,
    LessonLike,
    MediaItem,
    Post,
    PrayerRequest,
    Profile,
    Season,
    Series,
)

# -------------------------------------------------------------------
# Small utilities
# -------------------------------------------------------------------

def _paginate(request: HttpRequest, queryset, per_page: int = 10) -> Page:
    """Robust paginator with safe page handling."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page") or 1
    return paginator.get_page(page_number)


def _extract_youtube_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from common URL formats.
    Returns None if not a known format.
    """
    if not url:
        return None
    # Short youtu.be/<id>
    m = re.match(r"^https?://youtu\.be/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)
    # watch?v=<id>
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)
    # embed/<id>
    m = re.search(r"/embed/([A-Za-z0-9_-]{6,})", url)
    if m:
        return m.group(1)
    return None


def _referer_or(request: HttpRequest, default: str) -> str:
    return request.META.get("HTTP_REFERER") or default


# -------------------------------------------------------------------
# Public pages
# -------------------------------------------------------------------

def home(request: HttpRequest) -> HttpResponse:
    """Home page view"""
    featured_posts = (
        Post.objects.filter(status="published", featured=True)
        .select_related("category", "author")
        .order_by("-published_at", "-created_at")[:3]
    )
    upcoming_events = (
        Event.objects.filter(date__gte=timezone.now())
        .order_by("date")[:3]
    )
    context = {
        "featured_posts": featured_posts,
        "upcoming_events": upcoming_events,
        "current_year": timezone.now().year,
    }
    return render(request, "home.html", context)


def about(request: HttpRequest) -> HttpResponse:
    """About page view"""
    return render(request, "about.html")


def news(request: HttpRequest) -> HttpResponse:
    """
    News listing page with search + category filter + pagination.
    Optimized with select_related and annotate for quick lists.
    """
    posts = (
        Post.objects.filter(status="published")
        .select_related("category", "author")
        .order_by("-published_at", "-created_at")
    )
    categories = Category.objects.all().order_by("name")

    # Search
    search_query = (request.GET.get("search") or "").strip()
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query)
            | Q(content__icontains=search_query)
            | Q(excerpt__icontains=search_query)
        )

    # Category filter
    category_filter = (request.GET.get("category") or "").strip()
    if category_filter and category_filter != "all":
        posts = posts.filter(category__slug=category_filter)

    page_obj = _paginate(request, posts, per_page=6)

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "search_query": search_query,
        "category_filter": category_filter,
    }
    return render(request, "news/list.html", context)


def news_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """News detail page"""
    post = get_object_or_404(
        Post.objects.select_related("category", "author"),
        slug=slug,
        status="published",
    )

    # Increment views safely
    Post.objects.filter(pk=post.pk).update(views=post.views + 1)
    post.refresh_from_db(fields=["views"])

    related_posts = (
        Post.objects.filter(category=post.category, status="published")
        .exclude(pk=post.pk)
        .order_by("-published_at", "-created_at")[:3]
    )

    context = {"post": post, "related_posts": related_posts}
    return render(request, "news/detail.html", context)


def bible_studies(request: HttpRequest) -> HttpResponse:
    """
    Bible studies page:
    - Lists Seasons + Series (prefetched)
    - Lists Lessons with search/season filter + pagination
    """
    # Prefetch published lessons only to avoid heavy payload
    published_lessons_qs = Lesson.objects.filter(status="published").only(
        "id", "slug", "title", "order", "status", "series_id"
    )
    seasons = (
        Season.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch("series__lessons", queryset=published_lessons_qs)
        )
        .order_by("order", "-created_at")
    )

    lessons = (
        Lesson.objects.filter(status="published")
        .select_related("series", "series__season")
        .order_by("series__season__order", "series__order", "order", "-created_at")
    )

    # Search
    search_query = (request.GET.get("search") or "").strip()
    if search_query:
        lessons = lessons.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(bible_references__icontains=search_query)
        )

    # Season filter
    season_filter = (request.GET.get("season") or "").strip()
    if season_filter and season_filter != "all":
        lessons = lessons.filter(series__season__slug=season_filter)

    lessons_page = _paginate(request, lessons, per_page=9)

    context = {
        "seasons": seasons,
        "lessons_page": lessons_page,
        "search_query": search_query,
        "season_filter": season_filter,
    }
    return render(request, "bible_studies/list.html", context)


def events(request: HttpRequest) -> HttpResponse:
    """Events listing page with filters + pagination."""
    all_events = Event.objects.all().order_by("date")

    event_filter = (request.GET.get("filter") or "all").strip()
    now = timezone.now()
    if event_filter == "upcoming":
        events_list = all_events.filter(date__gte=now)
    elif event_filter == "featured":
        events_list = all_events.filter(is_featured=True)
    elif event_filter == "past":
        events_list = all_events.filter(date__lt=now)
    else:
        events_list = all_events

    page_obj = _paginate(request, events_list, per_page=6)
    context = {
        "page_obj": page_obj,
        "event_filter": event_filter,
    }
    return render(request, "events/list.html", context)


def event_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """Event detail page"""
    event = get_object_or_404(Event, slug=slug)
    return render(request, "events/detail.html", {"event": event})


def prayer_requests(request: HttpRequest) -> HttpResponse:
    """Prayer requests page"""
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
    """Donations page"""
    return render(request, "donations.html")

@login_required
def subscribe_toggle(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    # Tengeneza profile ikiwa haipo
    prof, _ = Profile.objects.get_or_create(user=request.user, defaults={"receive_notifications": True})
    prof.receive_notifications = not prof.receive_notifications
    prof.save(update_fields=["receive_notifications"])
    if prof.receive_notifications:
        messages.success(request, "Umejiunga na arifa za masomo mapya.")
    else:
        messages.info(request, "Umejiondoa kwenye arifa za masomo mapya.")
    return redirect(_referer_or(request, reverse("home")))

# -------------------------------------------------------------------
# Lesson detail + interactions (likes, comments)
# -------------------------------------------------------------------

def lesson_detail(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Lesson detail:
    - increments views
    - shows read/play/download CTAs depending on available content
    - lists comments
    - shows like state for logged-in users
    - computes a safe YouTube embed URL if video_url present
    """
    lesson = get_object_or_404(
        Lesson.objects.select_related("series", "series__season"),
        slug=slug,
        status="published",
    )

    # Increment views safely
    Lesson.objects.filter(pk=lesson.pk).update(views=lesson.views + 1)
    lesson.refresh_from_db(fields=["views"])

    # Related lessons in same series (ordered)
    related_lessons = (
        Lesson.objects.filter(series=lesson.series, status="published")
        .exclude(pk=lesson.pk)
        .only("id", "slug", "title", "order")
        .order_by("order")[:5]
    )

    user_has_liked = False
    if request.user.is_authenticated:
        user_has_liked = LessonLike.objects.filter(
            user=request.user, lesson=lesson
        ).exists()

    # Comments (approved first)
    comments = (
        lesson.lesson_comments.filter(is_approved=True)
        .select_related("user")
        .order_by("-created_at")
    )

    # Optional: simple throttle for comment spam (15s per lesson)
    comment_form = LessonCommentForm()
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Tafadhali ingia kwanza ili uache maoni.")
            return redirect(f"{reverse('login')}?next={request.path}")

        last_ts_key = f"last_comment_ts_{lesson.pk}"
        last_ts = request.session.get(last_ts_key)
        now_ts = int(timezone.now().timestamp())
        if last_ts and (now_ts - int(last_ts) < 15):
            messages.warning(request, "Umekuwa ukituma maoni haraka sana. Tafadhali jaribu tena baada ya muda mfupi.")
            return redirect("content:lesson_detail", slug=slug)

        comment_form = LessonCommentForm(request.POST)
        if comment_form.is_valid():
            c: LessonComment = comment_form.save(commit=False)
            c.user = request.user
            c.lesson = lesson
            c.save()
            request.session[last_ts_key] = now_ts
            messages.success(request, "Maoni yako yamehifadhiwa.")
            return redirect("content:lesson_detail", slug=slug)

    # YouTube embed helper
    youtube_id = _extract_youtube_id(lesson.video_url) if lesson.video_url else None
    embed_url = f"https://www.youtube.com/embed/{youtube_id}" if youtube_id else None

    return render(
        request,
        "bible_studies/detail.html",
        {
            "lesson": lesson,
            "related_lessons": related_lessons,
            "user_has_liked": user_has_liked,
            "comment_form": comment_form,
            "comments": comments,
            "youtube_id": youtube_id,
            "embed_url": embed_url,
        },
    )


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


# -------------------------------------------------------------------
# Accounts: signup + verify + subscription toggle
# -------------------------------------------------------------------

def signup_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                login(request, user)  # mruhusu aingie mara moja (email verification iko separate)
            messages.success(
                request,
                "Akaunti imeundwa. Tumekutumia barua pepe ya kukaribisha na ya kuthibitisha.",
            )
            return redirect("home")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


def verify_email_view(request: HttpRequest) -> HttpResponse:
    token = request.GET.get("token")
    if not token:
        return HttpResponseBadRequest("Missing token.")
    try:
        profile = Profile.objects.get(email_verification_token=token)
    except Profile.DoesNotExist:
        messages.error(request, "Token si sahihi au imeshatumika.")
        return redirect("home")

    # Optional expiry check (48h)
    if profile.token_created_at:
        age_hours = (timezone.now() - profile.token_created_at).total_seconds() / 3600.0
        if age_hours > 48:
            messages.error(request, "Token imeisha muda. Tafadhali omba uthibitisho upya.")
            return redirect("home")

    profile.email_verified = True
    profile.email_verification_token = ""
    profile.save(update_fields=["email_verified", "email_verification_token"])
    messages.success(request, "Barua pepe yako imethibitishwa. Asante!")
    return redirect("home")


@login_required
def subscribe_toggle(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")

    # Tengeneza Profile iwapo haipo (hii inaondoa RelatedObjectDoesNotExist)
    prof, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"receive_notifications": True}
    )

    prof.receive_notifications = not prof.receive_notifications
    prof.save(update_fields=["receive_notifications"])

    if prof.receive_notifications:
        messages.success(request, "Umejiunga na arifa za masomo mapya.")
    else:
        messages.info(request, "Umejiondoa kwenye arifa za masomo mapya.")

    return redirect(request.META.get("HTTP_REFERER", reverse("home")))

@login_required
def announcement_send_view(request: HttpRequest, pk: int) -> HttpResponse:
    # Send general announcement to all subscribers
    if not request.user.is_staff:
        return HttpResponseForbidden("Forbidden")
    ann = get_object_or_404(Announcement, pk=pk)

    from .utils.emailing import _send_html_email
    from django.contrib.auth.models import User

    users = User.objects.filter(profile__receive_notifications=True).select_related("profile")
    total = 0
    for u in users:
        _send_html_email(
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
