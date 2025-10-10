# content/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ===== DRF Router (weka tu kama ViewSets zipo) =====
try:
    from .views import (
        CategoryViewSet, PostViewSet, SeasonViewSet, SeriesViewSet,
        LessonViewSet, EventViewSet, MediaItemViewSet, PrayerRequestViewSet,
    )
    router = DefaultRouter()
    router.register(r'categories', CategoryViewSet, basename='category')
    router.register(r'posts', PostViewSet, basename='post')
    router.register(r'seasons', SeasonViewSet, basename='season')
    router.register(r'series', SeriesViewSet, basename='series')
    router.register(r'lessons', LessonViewSet, basename='lesson')
    router.register(r'events', EventViewSet, basename='event')
    router.register(r'media', MediaItemViewSet, basename='mediaitem')
    router.register(r'prayer-requests', PrayerRequestViewSet, basename='prayerrequest')
except Exception:
    router = DefaultRouter()  # endelea bila viewsets ikiwa bado hujazitengeneza

app_name = "content"

urlpatterns = [
    # Pages
    path("signup/", views.signup_view, name="signup"),
    path("verify-email/", views.verify_email_view, name="verify_email"),
    path("lessons/<slug:slug>/", views.lesson_detail, name="lesson_detail"),
    path("lessons/<slug:slug>/like/", views.lesson_like_toggle, name="lesson_like"),
    path("subscribe-toggle/", views.subscribe_toggle, name="subscribe_toggle"),
    path("announcements/<int:pk>/send/", views.announcement_send_view, name="announcement_send"),  # optional

    # API (under /api/)
    path("api/", include(router.urls)),
]
