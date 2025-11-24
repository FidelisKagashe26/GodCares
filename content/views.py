# backend/content/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from django.db.models import Q, Count, Prefetch, Sum
from django.utils import timezone

from .models import (
    Category, Post, Season, Series, Lesson, Event, MediaItem, PrayerRequest,
    LessonLike, LessonComment, Announcement, Profile, SiteSetting,
    DiscipleshipJourney, StageProgress, MissionReport, BibleStudyGroup,
    BaptismRecord, MissionMapLocation, Certificate, GlobalSoulsCounter
)
from .serializers import (
    CategorySerializer, PostListSerializer, PostDetailSerializer,
    SeriesSerializer, SeasonSerializer, LessonListSerializer, LessonDetailSerializer,
    EventSerializer, MediaItemSerializer, PrayerRequestSerializer,
    LessonCommentSerializer, LessonLikeSerializer, AnnouncementSerializer,
    ProfileSerializer, SiteSettingSerializer, DiscipleshipJourneySerializer,
    StageProgressSerializer, MissionReportSerializer, BibleStudyGroupSerializer,
    BaptismRecordSerializer, MissionMapLocationSerializer, CertificateSerializer,
    GlobalSoulsCounterSerializer
)
from .permissions import AdminOrReadOnly


# ==================== CONTENT VIEWSETS ====================

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["slug", "name"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("category", "author").all()
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "featured", "category", "author"]
    search_fields = ["title", "content", "excerpt"]
    ordering_fields = ["created_at", "published_at", "views", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status="published")
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostListSerializer

    @action(detail=True, methods=["post"])
    def increment_views(self, request, pk=None):
        post = self.get_object()
        post.views += 1
        post.save()
        return Response({"views": post.views})


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.prefetch_related("series").all()
    serializer_class = SeasonSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "slug"]
    search_fields = ["name", "description"]
    ordering_fields = ["order", "start_date", "created_at"]
    ordering = ["order"]


class SeriesViewSet(viewsets.ModelViewSet):
    queryset = Series.objects.select_related("season").prefetch_related("lessons").all()
    serializer_class = SeriesSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["season", "slug"]
    search_fields = ["name", "description"]
    ordering_fields = ["order", "created_at"]
    ordering = ["season", "order"]


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.select_related("series", "series__season").all()
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["series", "status", "series__season"]
    search_fields = ["title", "description", "content", "bible_references"]
    ordering_fields = ["order", "created_at", "views", "published_at"]
    ordering = ["series", "order"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(status="published")
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonDetailSerializer
        return LessonListSerializer

    @action(detail=True, methods=["post"])
    def increment_views(self, request, pk=None):
        lesson = self.get_object()
        lesson.views += 1
        lesson.save()
        return Response({"views": lesson.views})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def toggle_like(self, request, pk=None):
        lesson = self.get_object()
        like, created = LessonLike.objects.get_or_create(user=request.user, lesson=lesson)

        if not created:
            like.delete()
            return Response({"status": "unliked", "liked": False})

        return Response({"status": "liked", "liked": True})

    @action(detail=True, methods=["get"])
    def comments(self, request, pk=None):
        lesson = self.get_object()
        comments = lesson.lesson_comments.filter(is_approved=True).select_related("user")
        serializer = LessonCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def add_comment(self, request, pk=None):
        lesson = self.get_object()
        serializer = LessonCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, lesson=lesson)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_featured"]
    search_fields = ["title", "description", "location"]
    ordering_fields = ["date", "created_at"]
    ordering = ["date"]

    @action(detail=False)
    def upcoming(self, request):
        upcoming_events = self.get_queryset().filter(date__gte=timezone.now())
        serializer = self.get_serializer(upcoming_events, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def past(self, request):
        past_events = self.get_queryset().filter(date__lt=timezone.now())
        serializer = self.get_serializer(past_events, many=True)
        return Response(serializer.data)


class MediaItemViewSet(viewsets.ModelViewSet):
    queryset = MediaItem.objects.select_related("category").all()
    serializer_class = MediaItemSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["media_type", "category"]
    search_fields = ["title", "description", "tags"]
    ordering_fields = ["created_at", "views"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"])
    def increment_views(self, request, pk=None):
        media_item = self.get_object()
        media_item.views += 1
        media_item.save()
        return Response({"views": media_item.views})


class PrayerRequestViewSet(viewsets.ModelViewSet):
    queryset = PrayerRequest.objects.all()
    serializer_class = PrayerRequestSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "is_anonymous", "is_urgent", "is_answered"]
    search_fields = ["request", "name"]
    ordering_fields = ["created_at", "is_urgent"]
    ordering = ["-is_urgent", "-created_at"]

    def get_permissions(self):
        if self.action in ["update", "partial_update", "destroy"]:
            return [AdminOrReadOnly()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        if serializer.validated_data.get("is_anonymous"):
            serializer.save(name="", email="", phone="")
        else:
            serializer.save()


class LessonCommentViewSet(viewsets.ModelViewSet):
    queryset = LessonComment.objects.select_related("user", "lesson").all()
    serializer_class = LessonCommentSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["lesson", "user", "is_approved"]
    search_fields = ["body"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]


class LessonLikeViewSet(viewsets.ModelViewSet):
    queryset = LessonLike.objects.select_related("user", "lesson").all()
    serializer_class = LessonLikeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["lesson"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.select_related("sent_by").all()
    serializer_class = AnnouncementSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "body"]
    ordering_fields = ["created_at", "sent_at"]
    ordering = ["-created_at"]


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related("user").all()
    serializer_class = ProfileSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["email_verified", "receive_notifications"]
    search_fields = ["user__username", "user__email", "phone_number"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]


class SiteSettingViewSet(viewsets.ModelViewSet):
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [AdminOrReadOnly]

    def get_queryset(self):
        return SiteSetting.objects.filter(pk=1)


# ==================== MISSION PLATFORM VIEWSETS ====================

class DiscipleshipJourneyViewSet(viewsets.ModelViewSet):
    serializer_class = DiscipleshipJourneySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["current_stage", "seeker_completed", "scholar_completed", "missionary_completed"]
    ordering_fields = ["started_date", "completed_date"]
    ordering = ["started_date"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return DiscipleshipJourney.objects.select_related("user").all()
        return DiscipleshipJourney.objects.select_related("user").filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def advance_stage(self, request, pk=None):
        journey = self.get_object()
        current_stage = journey.current_stage

        stage_mapping = {
            "seeker": "scholar",
            "scholar": "missionary",
            "missionary": "missionary",
        }

        if current_stage in stage_mapping:
            journey.current_stage = stage_mapping[current_stage]

            if current_stage == "seeker":
                journey.seeker_completed = True
            elif current_stage == "scholar":
                journey.scholar_completed = True
            elif current_stage == "missionary":
                journey.missionary_completed = True
                journey.completed_date = timezone.now()

            journey.save()
            return Response({"status": "stage advanced", "new_stage": journey.current_stage})

        return Response({"error": "Cannot advance from current stage"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def update_progress(self, request, pk=None):
        journey = self.get_object()
        progress = request.data.get("progress", 0)

        try:
            progress = int(progress)
        except (TypeError, ValueError):
            return Response({"error": "Progress must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        if 0 <= progress <= 100:
            journey.progress_percentage = progress
            journey.save()
            return Response({"progress": journey.progress_percentage})

        return Response({"error": "Progress must be between 0 and 100"}, status=status.HTTP_400_BAD_REQUEST)


class StageProgressViewSet(viewsets.ModelViewSet):
    serializer_class = StageProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["journey", "stage", "completed", "lesson"]
    ordering_fields = ["completed_date"]
    ordering = ["lesson__order"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return StageProgress.objects.select_related("journey", "lesson").all()
        return StageProgress.objects.select_related("journey", "lesson").filter(journey__user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_completed(self, request, pk=None):
        stage_progress = self.get_object()
        stage_progress.completed = True
        stage_progress.completed_date = timezone.now()
        stage_progress.score = request.data.get("score", 100)
        stage_progress.notes = request.data.get("notes", "")
        stage_progress.save()

        return Response({"status": "completed", "score": stage_progress.score})


class MissionReportViewSet(viewsets.ModelViewSet):
    serializer_class = MissionReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["missionary", "location", "is_verified"]
    search_fields = ["title", "location", "testimonies", "challenges"]
    ordering_fields = ["date_conducted", "created_at"]
    ordering = ["-date_conducted"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return MissionReport.objects.select_related("missionary", "verified_by").all()
        return MissionReport.objects.select_related("missionary", "verified_by").filter(missionary=self.request.user)

    def perform_create(self, serializer):
        serializer.save(missionary=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def verify(self, request, pk=None):
        """
        Mark a mission report as verified.
        Global stats are updated via signals (see content.signals).
        """
        mission_report = self.get_object()
        if mission_report.is_verified:
            return Response({"status": "already verified"})

        mission_report.is_verified = True
        mission_report.verified_by = request.user
        mission_report.verified_at = timezone.now()
        mission_report.save()

        return Response({"status": "verified"})

    @action(detail=False)
    def stats(self, request):
        user_reports = self.get_queryset().filter(missionary=request.user)
        total_souls = user_reports.aggregate(Sum("souls_reached"))["souls_reached__sum"] or 0
        total_baptisms = user_reports.aggregate(Sum("baptisms_performed"))["baptisms_performed__sum"] or 0
        total_reports = user_reports.count()

        return Response(
            {
                "total_souls_reached": total_souls,
                "total_baptisms": total_baptisms,
                "total_reports": total_reports,
            }
        )


class BibleStudyGroupViewSet(viewsets.ModelViewSet):
    serializer_class = BibleStudyGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["leader", "is_active", "meeting_frequency"]
    search_fields = ["group_name", "description", "location"]
    ordering_fields = ["created_at", "current_members_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        base_qs = (
            BibleStudyGroup.objects.select_related("leader", "current_lesson")
            .prefetch_related("members")
        )

        user = self.request.user
        if not user.is_authenticated:
            return base_qs.none()

        action = getattr(self, "action", None)

        # Admin aone vyote / users waweze kuona vyote wakati wa join/leave/complete_lesson
        if user.is_staff or action in ["join", "leave", "complete_lesson"]:
            return base_qs.all()

        # Default: muone groups ambazo yeye ni leader au member
        return base_qs.filter(Q(leader=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        # leader ni current user, na anahesabiwa kama member pia
        group = serializer.save(leader=self.request.user, current_members_count=1)
        group.members.add(self.request.user)

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        group = self.get_object()
        if group.members.count() < group.max_members:
            group.members.add(request.user)
            group.current_members_count = group.members.count() + 1  # +1 leader
            group.save()
            return Response({"status": "joined group"})
        return Response({"error": "Group is full"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        group = self.get_object()
        if request.user != group.leader:
            group.members.remove(request.user)
            group.current_members_count = group.members.count() + 1
            group.save()
            return Response({"status": "left group"})
        return Response({"error": "Leader cannot leave group"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def complete_lesson(self, request, pk=None):
        group = self.get_object()
        lesson_id = request.data.get("lesson_id")

        try:
            lesson = Lesson.objects.get(id=lesson_id)
            group.lessons_completed.add(lesson)
            return Response({"status": "lesson completed"})
        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)


class BaptismRecordViewSet(viewsets.ModelViewSet):
    serializer_class = BaptismRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["missionary", "baptism_date"]
    search_fields = ["candidate_name", "location"]
    ordering_fields = ["baptism_date", "created_at"]
    ordering = ["-baptism_date"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return BaptismRecord.objects.select_related("missionary").all()
        return BaptismRecord.objects.select_related("missionary").filter(missionary=self.request.user)

    def perform_create(self, serializer):
        serializer.save(missionary=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_follow_up_completed(self, request, pk=None):
        baptism_record = self.get_object()
        baptism_record.follow_up_completed = True
        baptism_record.save()
        return Response({"status": "follow up completed"})


class MissionMapLocationViewSet(viewsets.ModelViewSet):
    serializer_class = MissionMapLocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["missionary", "visit_type"]
    ordering_fields = ["date_visited", "created_at"]
    ordering = ["-date_visited"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return MissionMapLocation.objects.select_related("missionary").all()
        return MissionMapLocation.objects.select_related("missionary").filter(missionary=self.request.user)

    def perform_create(self, serializer):
        serializer.save(missionary=self.request.user)

    @action(detail=False)
    def heatmap_data(self, request):
        locations = self.get_queryset()
        heatmap_data = []

        for location in locations:
            heatmap_data.append(
                {
                    "lat": location.gps_coordinates.get("lat"),
                    "lng": location.gps_coordinates.get("lng"),
                    "weight": location.souls_contacted,
                    "location_name": location.location_name,
                    "visit_type": location.visit_type,
                    "date": location.date_visited,
                }
            )

        return Response(heatmap_data)


class CertificateViewSet(viewsets.ModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["user", "certificate_type", "verified"]
    ordering_fields = ["issued_date", "created_at"]
    ordering = ["-issued_date"]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Certificate.objects.select_related("user", "issued_by").all()
        return Certificate.objects.select_related("user", "issued_by").filter(user=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def issue_certificate(self, request, pk=None):
        certificate = self.get_object()
        certificate.verified = True
        certificate.issued_by = request.user
        certificate.issued_date = timezone.now()
        certificate.save()

        return Response({"status": "certificate issued"})


class GlobalSoulsCounterViewSet(viewsets.ModelViewSet):
    queryset = GlobalSoulsCounter.objects.all()
    serializer_class = GlobalSoulsCounterSerializer
    permission_classes = [AdminOrReadOnly]

    def get_queryset(self):
        return GlobalSoulsCounter.objects.filter(pk=1)

    @action(detail=False)
    def dashboard_stats(self, request):
        global_counter = self.get_queryset().first()
        if not global_counter:
            global_counter = GlobalSoulsCounter.objects.create(pk=1)

        active_missionaries = DiscipleshipJourney.objects.filter(current_stage="missionary").count()
        active_groups = BibleStudyGroup.objects.filter(is_active=True).count()

        return Response(
            {
                "total_souls_reached": global_counter.total_souls_reached,
                "total_baptisms": global_counter.total_baptisms,
                "total_mission_reports": global_counter.total_mission_reports,
                "total_bible_study_groups": global_counter.total_bible_study_groups,
                "active_missionaries": active_missionaries,
                "active_groups": active_groups,
                "last_updated": global_counter.last_updated,
            }
        )


# ==================== EXTRA API VIEWS (for dashboard & global data) ====================

class UserDashboardAPIView(APIView):
    """
    Dashboard ya mtumiaji mmoja:
    - safari ya discipleship
    - activities za karibuni (missions, baptisms, groups, lessons).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        journey = DiscipleshipJourney.objects.filter(user=user).first()
        journey_data = DiscipleshipJourneySerializer(journey).data if journey else None

        recent_missions = MissionReport.objects.filter(missionary=user).order_by("-date_conducted")[:5]
        recent_baptisms = BaptismRecord.objects.filter(missionary=user).order_by("-baptism_date")[:5]
        groups = (
            BibleStudyGroup.objects.filter(Q(leader=user) | Q(members=user))
            .distinct()
            .order_by("-created_at")[:5]
        )
        recent_lessons = (
            StageProgress.objects.filter(journey__user=user, completed=True)
            .select_related("lesson")
            .order_by("-completed_date")[:5]
        )

        data = {
            "journey": journey_data,
            "recent_activity": {
                "missions": MissionReportSerializer(recent_missions, many=True).data,
                "baptisms": BaptismRecordSerializer(recent_baptisms, many=True).data,
                "groups": BibleStudyGroupSerializer(groups, many=True).data,
                "completed_lessons": StageProgressSerializer(recent_lessons, many=True).data,
            },
        }
        return Response(data)


class UserJourneyProgressAPIView(APIView):
    """
    Endpoint maalum wa kurudisha progress yote ya safari ya disciple wa current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        journey = DiscipleshipJourney.objects.filter(user=request.user).first()
        if not journey:
            return Response({"detail": "Journey not found."}, status=status.HTTP_404_NOT_FOUND)

        progress_qs = (
            StageProgress.objects.filter(journey=journey)
            .select_related("lesson")
            .order_by("lesson__order")
        )
        progress_data = StageProgressSerializer(progress_qs, many=True).data

        return Response(
            {
                "journey": DiscipleshipJourneySerializer(journey).data,
                "progress": progress_data,
            }
        )


class MissionHeatmapDataAPIView(APIView):
    """
    Endpoint rahisi wa heatmap data (kwa user au kwa staff wote).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.is_staff:
            locations = MissionMapLocation.objects.all()
        else:
            locations = MissionMapLocation.objects.filter(missionary=request.user)

        data = []
        for loc in locations:
            data.append(
                {
                    "lat": loc.gps_coordinates.get("lat"),
                    "lng": loc.gps_coordinates.get("lng"),
                    "weight": loc.souls_contacted,
                    "location_name": loc.location_name,
                    "visit_type": loc.visit_type,
                    "visit_type_display": loc.get_visit_type_display(),
                    "date": loc.date_visited,
                }
            )

        return Response(data)


class GlobalStatsAPIView(APIView):
    """
    Global stats kwa public (au app) – inaweza kutumika kwenye homepage ya website.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        global_counter, _ = GlobalSoulsCounter.objects.get_or_create(pk=1)

        journey_stats = DiscipleshipJourney.objects.aggregate(
            total_users=Count("id"),
            seekers=Count("id", filter=Q(current_stage="seeker")),
            scholars=Count("id", filter=Q(current_stage="scholar")),
            missionaries=Count("id", filter=Q(current_stage="missionary")),
            completed=Count("id", filter=Q(missionary_completed=True)),
        )

        active_groups = BibleStudyGroup.objects.filter(is_active=True).count()
        total_baptism_records = BaptismRecord.objects.count()

        return Response(
            {
                "global_counter": GlobalSoulsCounterSerializer(global_counter).data,
                "journey_stats": journey_stats,
                "active_groups": active_groups,
                "total_baptism_records": total_baptism_records,
            }
        )
