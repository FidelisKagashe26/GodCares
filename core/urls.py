# core/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r"system-settings", views.SystemSettingViewSet, basename="systemsetting"
)
router.register(
    r"user-activities", views.UserActivityViewSet, basename="useractivity"
)
router.register(
    r"user-profiles", views.UserProfileViewSet, basename="userprofile"
)

app_name = "core"

urlpatterns = [
    path("api/", include(router.urls)),

    path(
        "api/dashboard/stats/",
        views.DashboardStatsAPIView.as_view(),
        name="dashboard-stats",
    ),
    path("api/search/", views.site_search, name="site-search"),
    path("api/track-activity/", views.track_activity, name="track-activity"),
    path(
        "api/mission-progress/",
        views.MissionProgressAPIView.as_view(),
        name="mission-progress",
    ),

    path(
        "api/user/profile/me/",
        views.UserProfileViewSet.as_view({"get": "me", "put": "me"}),
        name="user-profile-me",
    ),
]
