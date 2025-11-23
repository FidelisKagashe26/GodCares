# progress/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LessonProgressViewSet,
    LevelProgressViewSet,
    MyProgressAPIView,
    MenteeProgressAPIView,
)

app_name = "progress_api"

router = DefaultRouter()
router.register(r"lesson-progress", LessonProgressViewSet, basename="lesson-progress")
router.register(r"level-progress", LevelProgressViewSet, basename="level-progress")

urlpatterns = [
    path("", include(router.urls)),
    path("me/", MyProgressAPIView.as_view(), name="my-progress"),
    path("mentee/<int:mentee_id>/", MenteeProgressAPIView.as_view(), name="mentee-progress"),
]
