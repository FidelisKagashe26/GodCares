from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, PostViewSet, SeasonViewSet, SeriesViewSet,
    LessonViewSet, EventViewSet, MediaItemViewSet, PrayerRequestViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'posts', PostViewSet, basename='post')
router.register(r'seasons', SeasonViewSet, basename='season')
router.register(r'series', SeriesViewSet, basename='series')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'events', EventViewSet, basename='event')
router.register(r'media', MediaItemViewSet)
router.register(r'prayer-requests', PrayerRequestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]