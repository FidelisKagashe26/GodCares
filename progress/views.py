# progress/api/views.py
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from discipleship.models import DiscipleshipLevel
from mentorship.models import Mentorship

from progress.models import LessonProgress, LevelProgress
from progress.serializers import (
    LessonProgressSerializer,
    LevelProgressSerializer,
    MyProgressResponseSerializer,
    MenteeProgressResponseSerializer,
)
from progress.services.tracker import (
    user_level_completion_percent,
    user_overall_completion,
)

User = get_user_model()


# ========= ViewSets za CRUD (mainly for API / admin) =========


class LessonProgressViewSet(viewsets.ModelViewSet):
    """
    CRUD ya LessonProgress.
    - Staff: wanaona record zote.
    - User wa kawaida: anaona zake tu.
    """

    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["lesson", "status"]
    ordering_fields = ["completed_at", "created_at"]
    ordering = ["-completed_at", "-created_at"]

    def get_queryset(self):
        # drf-spectacular hutumia swagger_fake_view wakati wa schema generation
        if getattr(self, "swagger_fake_view", False):
            return LessonProgress.objects.none()

        qs = LessonProgress.objects.select_related(
            "user",
            "lesson",
            "lesson__level",
            "lesson__level__path",
        )
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Kwa kawaida utatumia mark_lesson_complete(), lakini tunaacha hapa pia.
        serializer.save(user=self.request.user)


class LevelProgressViewSet(viewsets.ModelViewSet):
    """
    CRUD ya LevelProgress.
    """

    serializer_class = LevelProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["level", "status"]
    ordering_fields = ["completed_at", "created_at"]
    ordering = ["-completed_at", "-created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return LevelProgress.objects.none()

        qs = LevelProgress.objects.select_related(
            "user",
            "level",
            "level__path",
        )
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ========= High-level Progress APIs (Dashboard style) =========


class MyProgressAPIView(APIView):
    """
    GET /api/v1/progress/me/
    → Overview ya safari ya user:
      - list ya levels (Seeker/Scholar/Missionary + sub-levels) na %
      - summary ya masomo yote (done/total/overall_pct)
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses=MyProgressResponseSerializer,
        tags=["Progress"],
        summary="Get overall discipleship progress for the current user",
    )
    def get(self, request):
        user = request.user

        levels = (
            DiscipleshipLevel.objects.filter(is_active=True)
            .select_related("path")
            .prefetch_related("lessons")
        )

        levels_data = []
        for lv in levels:
            total_lessons = lv.lessons.filter(is_published=True).count()
            percent = user_level_completion_percent(user, lv)

            levels_data.append(
                {
                    "id": lv.id,
                    "name": lv.name,
                    "slug": lv.slug,
                    "description": lv.description,
                    "order": lv.order,
                    "path": {
                        "id": lv.path.id,
                        "name": lv.path.name,
                        "stage": lv.path.stage,
                        "stage_label": lv.path.get_stage_display(),
                    },
                    "total_lessons": total_lessons,
                    "percent": percent,
                }
            )

        done, total, overall_pct = user_overall_completion(user)

        payload = {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "levels": levels_data,
            "summary": {
                "lessons_completed": done,
                "total_lessons": total,
                "overall_percent": overall_pct,
            },
        }

        serializer = MyProgressResponseSerializer(payload)
        return Response(serializer.data)


class MenteeProgressAPIView(APIView):
    """
    GET /api/v1/progress/mentee/<mentee_id>/
    → Mentor anaangalia progress ya mentee wake.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses=MenteeProgressResponseSerializer,
        tags=["Progress"],
        summary="Get discipleship progress for a mentee of the current mentor",
    )
    def get(self, request, mentee_id: int):
        # Hakikisha requester ni mentor wa huyu mentee
        if not Mentorship.objects.filter(
            mentor=request.user, mentee_id=mentee_id
        ).exists():
            return Response(
                {"detail": "Huna ruhusa kuona progress ya mtumiaji huyu."},
                status=status.HTTP_403_FORBIDDEN,
            )

        mentee = get_object_or_404(User, pk=mentee_id)

        levels = (
            DiscipleshipLevel.objects.filter(is_active=True)
            .select_related("path")
            .prefetch_related("lessons")
        )

        levels_data = []
        for lv in levels:
            total_lessons = lv.lessons.filter(is_published=True).count()
            percent = user_level_completion_percent(mentee, lv)

            levels_data.append(
                {
                    "id": lv.id,
                    "name": lv.name,
                    "slug": lv.slug,
                    "description": lv.description,
                    "order": lv.order,
                    "path": {
                        "id": lv.path.id,
                        "name": lv.path.name,
                        "stage": lv.path.stage,
                        "stage_label": lv.path.get_stage_display(),
                    },
                    "total_lessons": total_lessons,
                    "percent": percent,
                }
            )

        done, total, overall_pct = user_overall_completion(mentee)

        payload = {
            "mentee": {
                "id": mentee.id,
                "username": mentee.username,
                "email": mentee.email,
                "first_name": mentee.first_name,
                "last_name": mentee.last_name,
            },
            "levels": levels_data,
            "summary": {
                "lessons_completed": done,
                "total_lessons": total,
                "overall_percent": overall_pct,
            },
        }

        serializer = MenteeProgressResponseSerializer(payload)
        return Response(serializer.data)
