# core/views.py
from django.db.models import Q, Count, Sum
from django.contrib.auth.models import User  # unaweza usihitajike sana, lakini si shida

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
    OpenApiParameter,
)

from .models import UserActivity, SystemSetting
from .serializers import (
    UserActivitySerializer,
    SystemSettingSerializer,
    UserProfileSerializer,
    DashboardStatsSerializer,
)
from content.models import (
    Post,
    Lesson,
    Event,
    MediaItem,
    DiscipleshipJourney,
    MissionReport,
    BibleStudyGroup,
    BaptismRecord,
    GlobalSoulsCounter,
    Profile,
)
from content.serializers import (
    PostListSerializer,
    LessonListSerializer,
    EventSerializer,
    DiscipleshipJourneySerializer,
    MissionReportSerializer,
)


class SystemSettingViewSet(viewsets.ModelViewSet):
    """
    API for system settings (admin only).
    """
    queryset = SystemSetting.objects.all()
    serializer_class = SystemSettingSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["key", "value", "description"]
    ordering_fields = ["key", "created_at"]
    ordering = ["key"]


class UserActivityViewSet(viewsets.ModelViewSet):
    """
    API to inspect user activity.
    Admins see all; regular users only see their own records.
    """
    queryset = UserActivity.objects.select_related("user").all()
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["user", "activity_type", "created_at"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API for user profile management.
    """
    queryset = Profile.objects.select_related("user").all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    @action(detail=False, methods=["get", "put"])
    def me(self, request):
        """
        GET/PUT profile ya user aliye-authenticated.
        """
        profile = request.user.profile

        if request.method == "GET":
            serializer = self.get_serializer(profile)
            return Response(serializer.data)

        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DashboardStatsAPIView(APIView):
    """
    API for dashboard statistics (per-user + global mission stats).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get dashboard statistics for the authenticated user",
        description=(
            "Returns per-user mission stats, global counters, "
            "recent missions and discipleship journey snapshot."
        ),
        responses=DashboardStatsSerializer,
        tags=["Core"],
    )
    def get(self, request):
        user = request.user

        # User-specific stats
        user_stats = {
            "mission_reports_count": MissionReport.objects.filter(
                missionary=user
            ).count(),
            "souls_reached": MissionReport.objects.filter(
                missionary=user
            ).aggregate(total=Sum("souls_reached"))["total"]
            or 0,
            "baptisms_performed": MissionReport.objects.filter(
                missionary=user
            ).aggregate(total=Sum("baptisms_performed"))["total"]
            or 0,
            "bible_study_groups_leading": BibleStudyGroup.objects.filter(
                leader=user, is_active=True
            ).count(),
            "baptism_records": BaptismRecord.objects.filter(
                missionary=user
            ).count(),
        }

        # Global stats (ensure record exists)
        global_stats = GlobalSoulsCounter.objects.first()
        if not global_stats:
            global_stats = GlobalSoulsCounter.objects.create(pk=1)

        # Recent missions
        recent_missions = MissionReport.objects.filter(
            missionary=user
        ).order_by("-created_at")[:5]
        recent_missions_serializer = MissionReportSerializer(
            recent_missions, many=True
        )

        # Discipleship journey
        try:
            journey = DiscipleshipJourney.objects.get(user=user)
            journey_serializer = DiscipleshipJourneySerializer(journey)
            journey_data = journey_serializer.data
        except DiscipleshipJourney.DoesNotExist:
            journey_data = None

        data = {
            "user_stats": user_stats,
            "global_stats": {
                "total_souls_reached": global_stats.total_souls_reached,
                "total_baptisms": global_stats.total_baptisms,
                "total_mission_reports": global_stats.total_mission_reports,
                "active_missionaries": global_stats.active_missionaries,
            },
            "recent_missions": recent_missions_serializer.data,
            "journey": journey_data,
        }

        serializer = DashboardStatsSerializer(instance=data)
        return Response(serializer.data)


@extend_schema(
    summary="Global search across gospel content",
    description=(
        "Search posts, lessons, events and mission reports using a simple keyword query."
    ),
    parameters=[
        OpenApiParameter(
            name="q",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Search keyword",
        )
    ],
    responses=inline_serializer(
        name="SiteSearchResponse",
        fields={
            "query": serializers.CharField(),
            "results": serializers.DictField(),
            "total_results": serializers.IntegerField(),
        },
    ),
    tags=["Core"],
)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def site_search(request):
    """
    Global search across gospel content (posts, lessons, events, mission reports).
    """
    query = request.GET.get("q", "").strip()
    results = {}

    if query:
        # Posts
        posts = Post.pub.published().filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(excerpt__icontains=query)
        )[:10]
        results["posts"] = PostListSerializer(posts, many=True).data

        # Lessons
        lessons = Lesson.pub.published().filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(content__icontains=query)
            | Q(bible_references__icontains=query)
        )[:10]
        results["lessons"] = LessonListSerializer(lessons, many=True).data

        # Events
        events = Event.objects.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(location__icontains=query)
        )[:10]
        results["events"] = EventSerializer(events, many=True).data

        # Mission Reports (limit access)
        mission_reports = MissionReport.objects.filter(
            Q(title__icontains=query)
            | Q(location__icontains=query)
            | Q(testimonies__icontains=query)
        )
        if not request.user.is_staff:
            mission_reports = mission_reports.filter(missionary=request.user)
        mission_reports = mission_reports[:10]
        results["mission_reports"] = MissionReportSerializer(
            mission_reports, many=True
        ).data

    total_results = sum(len(section) for section in results.values())

    return Response(
        {
            "query": query,
            "results": results,
            "total_results": total_results,
        }
    )


@extend_schema(
    summary="Track a single user activity event",
    description="Records a user activity event for analytics and engagement tracking.",
    request=inline_serializer(
        name="TrackActivityRequest",
        fields={
            "activity_type": serializers.CharField(),
            "description": serializers.CharField(required=False, allow_blank=True),
            "metadata": serializers.DictField(required=False),
        },
    ),
    responses=inline_serializer(
        name="TrackActivityResponse",
        fields={
            "status": serializers.CharField(),
        },
    ),
    tags=["Core"],
)
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def track_activity(request):
    """
    Track a single user activity event.
    """
    activity_type = request.data.get("activity_type")
    description = request.data.get("description", "")
    metadata = request.data.get("metadata", {})

    if not activity_type:
        return Response(
            {"error": "activity_type required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    ip_address = request.META.get("REMOTE_ADDR")
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    UserActivity.objects.create(
        user=request.user,
        activity_type=activity_type,
        description=description,
        metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return Response({"status": "activity tracked"})


class MissionProgressAPIView(APIView):
    """
    API for mission progress tracking (monthly & yearly per missionary).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get mission progress (monthly & yearly) for authenticated missionary",
        responses=inline_serializer(
            name="MissionProgressResponse",
            fields={
                "monthly": inline_serializer(
                    name="MissionProgressMonthly",
                    fields={
                        "missions": serializers.IntegerField(),
                        "souls_reached": serializers.IntegerField(),
                        "baptisms": serializers.IntegerField(),
                    },
                ),
                "yearly": inline_serializer(
                    name="MissionProgressYearly",
                    fields={
                        "missions": serializers.IntegerField(),
                        "souls_reached": serializers.IntegerField(),
                        "baptisms": serializers.IntegerField(),
                    },
                ),
            },
        ),
        tags=["Core"],
    )
    def get(self, request):
        from django.utils import timezone
        from datetime import timedelta

        user = request.user

        # Month range
        current_month = timezone.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        next_month = (current_month + timedelta(days=32)).replace(day=1)

        monthly_stats = MissionReport.objects.filter(
            missionary=user,
            date_conducted__gte=current_month,
            date_conducted__lt=next_month,
        ).aggregate(
            missions=Count("id"),
            souls=Sum("souls_reached"),
            baptisms=Sum("baptisms_performed"),
        )

        # Year range
        current_year = timezone.now().replace(
            month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        next_year = current_year.replace(year=current_year.year + 1)

        yearly_stats = MissionReport.objects.filter(
            missionary=user,
            date_conducted__gte=current_year,
            date_conducted__lt=next_year,
        ).aggregate(
            missions=Count("id"),
            souls=Sum("souls_reached"),
            baptisms=Sum("baptisms_performed"),
        )

        return Response(
            {
                "monthly": {
                    "missions": monthly_stats["missions"] or 0,
                    "souls_reached": monthly_stats["souls"] or 0,
                    "baptisms": monthly_stats["baptisms"] or 0,
                },
                "yearly": {
                    "missions": yearly_stats["missions"] or 0,
                    "souls_reached": yearly_stats["souls"] or 0,
                    "baptisms": yearly_stats["baptisms"] or 0,
                },
            }
        )
