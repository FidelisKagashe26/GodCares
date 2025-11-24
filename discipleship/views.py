# discipleship/views.py
from django.utils import timezone
from django.db.models import Count
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    DiscipleshipPath,
    DiscipleshipLevel,
    DiscipleshipLesson,
    LessonProgress,
    PathEnrollment,
    Quiz,
    QuizAttempt,
)
from .serializers import (
    DiscipleshipPathSerializer,
    DiscipleshipLevelSerializer,
    DiscipleshipLessonListSerializer,
    DiscipleshipLessonDetailSerializer,
    LessonProgressSerializer,
    PathEnrollmentSerializer,
    QuizSerializer,
    QuizAttemptSerializer,
)

# Tunatumia permission ile ile kama content
from content.permissions import AdminOrReadOnly


class DiscipleshipPathViewSet(viewsets.ModelViewSet):
    """
    CRUD ya Discipleship Paths (Seeker / Scholar / Missionary)
    """
    queryset = DiscipleshipPath.objects.all().order_by("order")
    serializer_class = DiscipleshipPathSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["stage", "is_active"]
    search_fields = ["name", "description"]
    ordering_fields = ["order", "created_at"]
    ordering = ["order"]


class DiscipleshipLevelViewSet(viewsets.ModelViewSet):
    """
    Levels ndani ya Path
    """
    queryset = (
        DiscipleshipLevel.objects.select_related("path")
        .all()
        .order_by("path__order", "order")
    )
    serializer_class = DiscipleshipLevelSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["path", "is_active"]
    search_fields = ["name", "description", "path__name"]
    ordering_fields = ["order", "created_at"]
    ordering = ["path__order", "order"]


class DiscipleshipLessonViewSet(viewsets.ModelViewSet):
    """
    Lessons per level + actions za kuanza/kucomplete
    """
    queryset = DiscipleshipLesson.objects.select_related(
        "level", "level__path"
    ).all()
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["level", "level__path", "is_published"]
    search_fields = ["title", "description", "bible_references", "level__name"]
    ordering_fields = ["order", "created_at", "duration_minutes"]
    ordering = ["level__path__order", "level__order", "order"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Watumiaji wa kawaida waone published only
        if not self.request.user.is_staff:
            qs = qs.filter(is_published=True)
        return qs

    def get_serializer_class(self):
        if self.action in ["retrieve", "create", "update", "partial_update"]:
            return DiscipleshipLessonDetailSerializer
        return DiscipleshipLessonListSerializer

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def start(self, request, pk=None):
        """
        Muanzishe LessonProgress (status = in_progress)
        """
        lesson = self.get_object()
        progress, _ = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
        )
        progress.mark_started()
        serializer = LessonProgressSerializer(progress)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def complete(self, request, pk=None):
        """
        Mark lesson as completed + update PathEnrollment progress
        """
        lesson = self.get_object()
        # Optional score from request
        raw_score = request.data.get("score", 100)
        try:
            score = int(raw_score)
        except (ValueError, TypeError):
            score = 100

        progress, _ = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
        )
        progress.mark_completed(score=score)

        # Ensure enrollment on this path
        path = lesson.level.path
        enrollment, _ = PathEnrollment.objects.get_or_create(
            user=request.user,
            path=path,
            defaults={"current_level": lesson.level},
        )
        # update current_level kama hii level iko mbele
        if (
            enrollment.current_level is None
            or enrollment.current_level.order <= lesson.level.order
        ):
            enrollment.current_level = lesson.level
        enrollment.update_progress()

        serializer = LessonProgressSerializer(progress)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def my_progress(self, request, pk=None):
        """
        Rudisha progress ya current user kwenye lesson hii
        """
        lesson = self.get_object()
        progress = LessonProgress.objects.filter(
            user=request.user, lesson=lesson
        ).first()
        if not progress:
            return Response(
                {"status": "not_started"},
                status=status.HTTP_200_OK,
            )
        serializer = LessonProgressSerializer(progress)
        return Response(serializer.data)


class LessonProgressViewSet(viewsets.ModelViewSet):
    """
    View & manage LessonProgress.
    - Admin: anaona zote
    - User: anaona zake tu
    """
    serializer_class = LessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = [
        "status",
        "lesson",
        "lesson__level",
        "lesson__level__path",
    ]
    ordering_fields = ["created_at", "completed_at", "score"]
    ordering = ["-created_at"]

    def get_queryset(self):
        # Muhimu kwa drf-spectacular wakati wa kujenga schema
        if getattr(self, "swagger_fake_view", False):
            return LessonProgress.objects.none()

        qs = LessonProgress.objects.select_related(
            "user", "lesson", "lesson__level", "lesson__level__path"
        )
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_completed(self, request, pk=None):
        progress = self.get_object()
        if progress.user != request.user and not request.user.is_staff:
            return Response(
                {"detail": "Not allowed"},
                status=status.HTTP_403_FORBIDDEN,
            )
        raw_score = request.data.get("score", progress.score or 100)
        try:
            score = int(raw_score)
        except (ValueError, TypeError):
            score = progress.score or 100

        progress.mark_completed(score=score)

        # update enrollment
        path = progress.lesson.level.path
        enrollment, _ = PathEnrollment.objects.get_or_create(
            user=progress.user,
            path=path,
            defaults={"current_level": progress.lesson.level},
        )
        enrollment.update_progress()

        serializer = LessonProgressSerializer(progress)
        return Response(serializer.data)


class PathEnrollmentViewSet(viewsets.ModelViewSet):
    """
    Enrollment kwenye paths.
    - User anaona / anadhibiti za kwake
    - Admin anaona zote
    """
    serializer_class = PathEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["path", "is_active"]
    ordering_fields = ["enrolled_at", "progress_percentage"]
    ordering = ["-enrolled_at"]

    def get_queryset(self):
        # Muhimu kwa drf-spectacular wakati wa kujenga schema
        if getattr(self, "swagger_fake_view", False):
            return PathEnrollment.objects.none()

        qs = PathEnrollment.objects.select_related(
            "user", "path", "current_level"
        )
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Hakikisha user ha-enroll mara mbili path moja
        path = serializer.validated_data["path"]
        existing = PathEnrollment.objects.filter(
            user=self.request.user,
            path=path,
        ).first()
        if existing:
            raise Exception("Already enrolled in this path.")
        # auto set current_level = level ya kwanza ikiwa haijawekwa
        enrollment = serializer.save(user=self.request.user)
        first_level = (
            DiscipleshipLevel.objects.filter(path=path, is_active=True)
            .order_by("order")
            .first()
        )
        if first_level and enrollment.current_level is None:
            enrollment.current_level = first_level
            enrollment.save()

    @action(detail=False, methods=["get"])
    def my_active(self, request):
        """
        Enrollments active za current user tu
        """
        qs = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class QuizViewSet(viewsets.ModelViewSet):
    """
    Quiz za lessons.
    - Watumiaji: wanasoma & kusubmit attempts
    - Admin: anaunda / anaedit
    """
    queryset = Quiz.objects.select_related(
        "lesson", "lesson__level", "lesson__level__path"
    )
    serializer_class = QuizSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["lesson", "is_active"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def submit(self, request, pk=None):
        """
        User anatuma majibu ya quiz.

        Body inatarajiwa:
        {
          "answers": {
            "question_id": [choice_ids] / "true"/"false"/"some text",
            ...
          },
          "time_spent_minutes": 5
        }
        """
        quiz = self.get_object()
        user = request.user

        # Max attempts check
        attempts_count = QuizAttempt.objects.filter(user=user, quiz=quiz).count()
        if quiz.max_attempts and attempts_count >= quiz.max_attempts:
            return Response(
                {"detail": "Maximum attempts reached for this quiz."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answers = request.data.get("answers", {}) or {}
        time_spent = request.data.get("time_spent_minutes", 0)

        # Simple grading logic
        total_points = quiz.questions.aggregate(total=Count("points"))["total"] or 0
        if total_points == 0:
            # Fallback: one point per question
            total_points = quiz.questions.count()

        score_points = 0

        for question in quiz.questions.all():
            q_key = str(question.id)
            user_answer = answers.get(q_key)

            if question.question_type == "multiple_choice":
                # user_answer can be id or list of ids
                if user_answer is None:
                    continue
                if not isinstance(user_answer, list):
                    user_answer = [user_answer]
                try:
                    user_ids = {int(x) for x in user_answer}
                except (ValueError, TypeError):
                    user_ids = set()

                correct_ids = set(
                    question.choices.filter(is_correct=True).values_list("id", flat=True)
                )
                if correct_ids and user_ids == correct_ids:
                    score_points += question.points

            elif question.question_type == "true_false":
                if user_answer is None:
                    continue
                answer_str = str(user_answer).lower()
                chosen_true = None
                if answer_str in ["true", "t", "1", "yes"]:
                    chosen_true = True
                elif answer_str in ["false", "f", "0", "no"]:
                    chosen_true = False

                correct_choice = question.choices.filter(is_correct=True).first()
                if correct_choice and chosen_true is not None:
                    correct_is_true = (
                        correct_choice.choice_text.strip().lower().startswith("t")
                    )
                    if chosen_true == correct_is_true:
                        score_points += question.points

            else:
                # short_answer – kwa sasa hatu-auto-grade
                continue

        if total_points > 0:
            percent_score = int(round((score_points / total_points) * 100))
        else:
            percent_score = 0

        passed = percent_score >= quiz.passing_score

        attempt = QuizAttempt.objects.create(
            user=user,
            quiz=quiz,
            score=percent_score,
            passed=passed,
            completed_at=timezone.now(),
            time_spent_minutes=time_spent or 0,
            answers=answers,
        )

        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Attempts za quizzes.
    - User: anaona attempts zake
    - Admin: anaona zote
    """
    serializer_class = QuizAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["quiz", "quiz__lesson", "passed"]
    ordering_fields = ["started_at", "score"]
    ordering = ["-started_at"]

    def get_queryset(self):
        # Muhimu kwa drf-spectacular wakati wa kujenga schema
        if getattr(self, "swagger_fake_view", False):
            return QuizAttempt.objects.none()

        qs = QuizAttempt.objects.select_related(
            "user", "quiz", "quiz__lesson"
        ).all()
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)
