# content/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for API endpoints
router = DefaultRouter()

# Content endpoints
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'posts', views.PostViewSet, basename='post')
router.register(r'seasons', views.SeasonViewSet, basename='season')
router.register(r'series', views.SeriesViewSet, basename='series')
router.register(r'lessons', views.LessonViewSet, basename='lesson')
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'media', views.MediaItemViewSet, basename='media')
router.register(r'prayer-requests', views.PrayerRequestViewSet, basename='prayerrequest')
router.register(r'lesson-comments', views.LessonCommentViewSet, basename='lessoncomment')
router.register(r'lesson-likes', views.LessonLikeViewSet, basename='lessonlike')
router.register(r'announcements', views.AnnouncementViewSet, basename='announcement')
router.register(r'profiles', views.ProfileViewSet, basename='profile')
router.register(r'site-settings', views.SiteSettingViewSet, basename='sitesetting')

# Mission Platform endpoints
router.register(r'discipleship-journeys', views.DiscipleshipJourneyViewSet, basename='discipleshipjourney')
router.register(r'stage-progress', views.StageProgressViewSet, basename='stageprogress')
router.register(r'mission-reports', views.MissionReportViewSet, basename='missionreport')
router.register(r'bible-study-groups', views.BibleStudyGroupViewSet, basename='biblestudygroup')
router.register(r'baptism-records', views.BaptismRecordViewSet, basename='baptismrecord')
router.register(r'mission-map-locations', views.MissionMapLocationViewSet, basename='missionmaplocation')
router.register(r'certificates', views.CertificateViewSet, basename='certificate')
router.register(r'global-souls-counter', views.GlobalSoulsCounterViewSet, basename='globalsoulscounter')

app_name = "content"

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Custom API actions
    path('api/user/dashboard/', views.UserDashboardAPIView.as_view(), name='user-dashboard'),
    path('api/user/journey-progress/', views.UserJourneyProgressAPIView.as_view(), name='user-journey-progress'),
    path('api/mission/heatmap-data/', views.MissionHeatmapDataAPIView.as_view(), name='mission-heatmap-data'),
    path('api/global/stats/', views.GlobalStatsAPIView.as_view(), name='global-stats'),
]