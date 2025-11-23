# discipleship/urls.py  (weka kama discipleship/api/urls.py kwenye project)
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "discipleship"

router = DefaultRouter()
router.register(r"paths", views.DiscipleshipPathViewSet, basename="path")
router.register(r"levels", views.DiscipleshipLevelViewSet, basename="level")
router.register(r"lessons", views.DiscipleshipLessonViewSet, basename="lesson")
router.register(r"lesson-progress", views.LessonProgressViewSet, basename="lessonprogress")
router.register(r"path-enrollments", views.PathEnrollmentViewSet, basename="pathenrollment")
router.register(r"quizzes", views.QuizViewSet, basename="quiz")
router.register(r"quiz-attempts", views.QuizAttemptViewSet, basename="quizattempt")

urlpatterns = [
    # /api/v1/discipleship/api/...
    path("api/", include(router.urls)),
]
