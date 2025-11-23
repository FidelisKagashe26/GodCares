# discipleship/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone


class DiscipleshipPath(models.Model):
    """
    Discipleship paths (Seeker, Scholar, Missionary)
    - Hapa ndo tunalinka na spiritual stages:
      seeker → scholar → missionary
    """
    STAGE_CHOICES = [
        ('seeker', '📘 Discover Truth - God Cares 365 Student'),
        ('scholar', '📖 Understand Prophecy - God Cares 365 Prophecy Student'),
        ('missionary', '🌍 Live & Share Message - God Cares 365 Missionary'),
    ]

    name = models.CharField(max_length=100)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='discipleship/paths/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Discipleship Path"
        verbose_name_plural = "Discipleship Paths"
        ordering = ['order']

    def __str__(self) -> str:
        return f"{self.get_stage_display()} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class DiscipleshipLevel(models.Model):
    """
    Levels ndani ya kila path (mfano:
    - Seeker Level 1, 2, 3...
    - Scholar Level 1, 2...
    """
    path = models.ForeignKey(
        DiscipleshipPath,
        on_delete=models.CASCADE,
        related_name='levels',
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True)
    description = models.TextField()
    order = models.PositiveIntegerField(default=0)
    required_score = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Discipleship Level"
        verbose_name_plural = "Discipleship Levels"
        ordering = ['path', 'order']
        unique_together = ['path', 'slug']

    def __str__(self) -> str:
        return f"{self.path.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class DiscipleshipLesson(models.Model):
    """
    Somo ndani ya Level fulani
    """
    level = models.ForeignKey(
        DiscipleshipLevel,
        on_delete=models.CASCADE,
        related_name='lessons',
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    description = models.TextField()
    content = models.TextField()
    video_url = models.URLField(blank=True)
    audio_url = models.URLField(blank=True)
    pdf_file = models.FileField(
        upload_to='discipleship/lessons/pdfs/',
        blank=True,
        null=True,
    )
    duration_minutes = models.PositiveIntegerField(default=0)
    bible_references = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    points_value = models.PositiveIntegerField(default=10)
    is_published = models.BooleanField(default=True)
    requires_previous = models.BooleanField(
        default=True,
        help_text="Kama true, lazima previous lesson iwe completed kabla ya hii.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Discipleship Lesson"
        verbose_name_plural = "Discipleship Lessons"
        ordering = ['level', 'order']
        unique_together = ['level', 'slug']

    def __str__(self) -> str:
        return f"{self.level.name} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def has_video(self) -> bool:
        return bool(self.video_url)

    @property
    def has_audio(self) -> bool:
        return bool(self.audio_url)

    @property
    def has_pdf(self) -> bool:
        return bool(self.pdf_file)


class LessonProgress(models.Model):
    """
    Track progress ya user kwenye kila Lesson
    """
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='discipleship_lesson_progress',
    )
    lesson = models.ForeignKey(
        DiscipleshipLesson,
        on_delete=models.CASCADE,
        related_name='progress',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started',
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    time_spent_minutes = models.PositiveIntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Lesson Progress"
        verbose_name_plural = "Lesson Progress"
        unique_together = ['user', 'lesson']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['lesson', 'status']),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.lesson.title} - {self.status}"

    def mark_started(self):
        if not self.started_at:
            self.started_at = timezone.now()
        if self.status == 'not_started':
            self.status = 'in_progress'
        self.save()

    def mark_completed(self, score: int = 100):
        self.status = 'completed'
        self.score = score
        now = timezone.now()
        self.completed_at = now
        if not self.started_at:
            self.started_at = now
        self.save()


class PathEnrollment(models.Model):
    """
    User ka-enroll kwenye Path gani?
    - progress_percentage inahesabiwa kulingana na LessonProgress
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='path_enrollments',
    )
    path = models.ForeignKey(
        DiscipleshipPath,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    current_level = models.ForeignKey(
        DiscipleshipLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    progress_percentage = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Path Enrollment"
        verbose_name_plural = "Path Enrollments"
        unique_together = ['user', 'path']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.path.name}"

    def update_progress(self):
        """
        Rekebisha progress_percentage kulingana na idadi ya
        lessons zilizomalizika kwenye path hii.
        """
        total_lessons = DiscipleshipLesson.objects.filter(
            level__path=self.path,
            is_published=True,
        ).count()

        if total_lessons == 0:
            self.progress_percentage = 0
            self.completed_at = None
        else:
            completed_lessons = LessonProgress.objects.filter(
                user=self.user,
                lesson__level__path=self.path,
                status__in=['completed', 'verified'],
            ).count()
            self.progress_percentage = int((completed_lessons / total_lessons) * 100)

            if self.progress_percentage >= 100 and not self.completed_at:
                self.completed_at = timezone.now()

        self.save()


class Quiz(models.Model):
    """
    Quiz ya somo moja (One-to-one na Lesson)
    """
    lesson = models.OneToOneField(
        DiscipleshipLesson,
        on_delete=models.CASCADE,
        related_name='quiz',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    passing_score = models.PositiveIntegerField(default=70)
    time_limit_minutes = models.PositiveIntegerField(default=30)
    max_attempts = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self) -> str:
        return f"{self.lesson.title} - {self.title}"


class QuizQuestion(models.Model):
    """
    Swali moja ndani ya Quiz
    """
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    ]

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    explanation = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Quiz Question"
        verbose_name_plural = "Quiz Questions"
        ordering = ['quiz', 'order']

    def __str__(self) -> str:
        return f"{self.quiz.title} - {self.question_text[:50]}"


class QuizChoice(models.Model):
    """
    Choice moja kwa swali la Multiple Choice / True/False
    """
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name='choices',
    )
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Quiz Choice"
        verbose_name_plural = "Quiz Choices"
        ordering = ['question', 'order']

    def __str__(self) -> str:
        return f"{self.question.question_text[:30]} - {self.choice_text}"


class QuizAttempt(models.Model):
    """
    Jaribio moja la mtumiaji kwenye Quiz
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
    )
    score = models.PositiveIntegerField(default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(default=0)
    answers = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Quiz Attempt"
        verbose_name_plural = "Quiz Attempts"
        ordering = ['-started_at']

    def __str__(self) -> str:
        return f"{self.user.username} - {self.quiz.title} - {self.score}%"
