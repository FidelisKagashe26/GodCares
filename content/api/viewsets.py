# content/api/viewsets.py
from django.db.models import Count, Exists, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from content.models import (
    Category, Post, Series, Season, Lesson, Event, MediaItem,
    PrayerRequest, LessonLike, LessonComment
)
from .serializers import (
    CategorySerializer, PostListSerializer, PostDetailSerializer,
    SeriesSerializer, SeasonSerializer,
    LessonListSerializer, LessonDetailSerializer,
    EventSerializer, MediaItemSerializer,
    PrayerRequestSerializer, LessonCommentSerializer
)
from .filters import PostFilter, LessonFilter, EventFilter
from content.permissions import AdminOrReadOnly


class BasePublicQuerysetMixin:
    """Kwa GET bila staff, rudisha tu yaliyopublished endapo model ina is_published."""
    published_field = "is_published"

    def get_queryset(self):
        qs = super().get_queryset()
        request = getattr(self, "request", None)
        if request and (not request.user.is_staff):
            Model = self.queryset.model if hasattr(self, "queryset") else None
            if Model and hasattr(Model, self.published_field):
                qs = qs.filter(**{self.published_field: True})
        return qs


class CategoryViewSet(BasePublicQuerysetMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name", "id")
    serializer_class = CategorySerializer
    permission_classes = [AdminOrReadOnly]
    filterset_fields = ["slug", "name"]
    search_fields = ["name"]
    ordering_fields = ["name", "id"]


class PostViewSet(BasePublicQuerysetMixin, viewsets.ModelViewSet):
    queryset = Post.objects.select_related("category").all().order_by("-id")
    permission_classes = [AdminOrReadOnly]
    filterset_class = PostFilter
    search_fields = ["title", "excerpt", "content"]
    ordering_fields = ["published_at", "title", "id"]

    def get_serializer_class(self):
        return PostListSerializer if self.action == "list" else PostDetailSerializer


class SeriesViewSet(BasePublicQuerysetMixin, viewsets.ModelViewSet):
    queryset = Series.objects.all().order_by("name", "id")
    serializer_class = SeriesSerializer
    permission_classes = [AdminOrReadOnly]
    filterset_fields = ["slug", "name"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "id"]


class SeasonViewSet(BasePublicQuerysetMixin, viewsets.ModelViewSet):
    # NB: Season ina 'order' (sio 'number')
    queryset = Season.objects.select_related("series").all().order_by("order", "id")
    serializer_class = SeasonSerializer
    permission_classes = [AdminOrReadOnly]
    filterset_fields = ["series", "slug", "name", "order", "is_active", "start_date", "end_date"]
    search_fields = ["name", "description"]
    ordering_fields = ["order", "id", "start_date", "end_date"]


class LessonViewSet(BasePublicQuerysetMixin, viewsets.ModelViewSet):
    queryset = Lesson.objects.select_related("series").all().order_by("-id")
    permission_classes = [AdminOrReadOnly]
    filterset_class = LessonFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "updated_at", "views", "title", "id"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)

        likes_sq = (
            LessonLike.objects
            .filter(lesson=OuterRef("pk"))
            .values("lesson")
            .annotate(c=Count("*"))
            .values("c")
        )
        comments_sq = (
            LessonComment.objects
            .filter(lesson=OuterRef("pk"), is_published=True)
            .values("lesson")
            .annotate(c=Count("*"))
            .values("c")
        )

        qs = qs.annotate(
            likes_count=Coalesce(Subquery(likes_sq, output_field=IntegerField()), 0),
            comments_count=Coalesce(Subquery(comments_sq, output_field=IntegerField()), 0),
        )

        if user and user.is_authenticated:
            qs = qs.annotate(is_liked=Exists(LessonLike.objects.filter(lesson=OuterRef("pk"), user=user)))
        else:
            qs = qs.annotate(is_liked=Exists(LessonLike.objects.filter(pk=0)))
        return qs

    def get_serializer_class(self):
        return LessonListSerializer if self.action == "list" else LessonDetailSerializer

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like_toggle(self, request, pk=None):
        obj = self.get_object()
        like, created = LessonLike.objects.get_or_create(user=request.user, lesson=obj)
        if not created:
            like.delete()
            return Response({"detail": "unliked"}, status=status.HTTP_200_OK)
        return Response({"detail": "liked"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "post"], permission_classes=[IsAuthenticatedOrReadOnly])
    def comments(self, request, pk=None):
        obj = self.get_object()
        if request.method.lower() == "get":
            qs = LessonComment.objects.filter(lesson=obj, is_published=True).order_by("-id")
            return Response(LessonCommentSerializer(qs, many=True).data)
        ser = LessonCommentSerializer(data=request.data)
        if ser.is_valid():
            ser.save(user=request.user, lesson=obj, is_published=False)
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class EventViewSet(BasePublicQuerysetMixin, viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by("-id")
    serializer_class = EventSerializer
    permission_classes = [AdminOrReadOnly]
    filterset_class = EventFilter
    search_fields = ["title", "location"]
    ordering_fields = ["id", "start_date", "end_date"]


class MediaItemViewSet(BasePublicQuerysetMixin, viewsets.ModelViewSet):
    queryset = MediaItem.objects.all().order_by("-id")
    serializer_class = MediaItemSerializer
    permission_classes = [AdminOrReadOnly]
    search_fields = ["title", "url"]
    ordering_fields = ["id", "title"]


class PrayerRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = PrayerRequest.objects.all().order_by("-id")
    serializer_class = PrayerRequestSerializer
    permission_classes = [AdminOrReadOnly]
    # MUHIMU: usitumie filterset_fields kwa majina yasiyo ya model
    search_fields = ["name", "topic", "message"]
    ordering_fields = ["id", "created_at"]
