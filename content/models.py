# content/models.py
from __future__ import annotations

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import RegexValidator, FileExtensionValidator
from django.urls import reverse
from django.db.models.functions import Lower

# ----------------- Helpers -----------------
def unique_slugify(instance, value, slug_field_name: str = "slug", max_length: int = 200):
    """
    Tengeneza slug ya kipekee. Ikiwa ipo, ongeza -2, -3, ...
    Hutumia Lower(...) constraint kwa case-insensitive uniqueness.
    """
    base_slug = slugify(value)[: max_length]
    slug = base_slug or "item"
    ModelClass = instance.__class__
    n = 2
    lookup = {f"{slug_field_name}__iexact": slug}
    while ModelClass.objects.filter(**lookup).exclude(pk=instance.pk).exists():
        suffix = f"-{n}"
        slug = (base_slug[: max_length - len(suffix)] + suffix).rstrip("-")
        lookup = {f"{slug_field_name}__iexact": slug}
        n += 1
    setattr(instance, slug_field_name, slug)


def image_validator():
    return FileExtensionValidator(allowed_extensions=("jpg", "jpeg", "png", "webp", "gif"))


def pdf_validator():
    return FileExtensionValidator(allowed_extensions=("pdf",))


def audio_validator():
    return FileExtensionValidator(allowed_extensions=("mp3", "wav", "m4a", "aac", "ogg"))


# ----------------- Managers -----------------
class PublishedQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status="published")


class PublishedManager(models.Manager):
    def get_queryset(self):
        return PublishedQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()


# ---------------- Existing Models (unaletwa kutoka kwako) ----------------

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [models.Index(Lower('slug'), name='category_slug_lower_idx')]
        constraints = [
            models.UniqueConstraint(Lower('slug'), name='category_slug_ci_unique')
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.name, max_length=100)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=300, blank=True)
    featured_image = models.ImageField(upload_to='posts/', blank=True, null=True, validators=[image_validator()])
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    objects = models.Manager()
    pub = PublishedManager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'status']),
            models.Index(Lower('slug'), name='post_slug_lower_idx'),
        ]
        constraints = [
            models.UniqueConstraint(Lower('slug'), name='post_slug_ci_unique')
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.title, max_length=200)
        if not self.excerpt and self.content:
            self.excerpt = self.content[:297] + '...' if len(self.content) > 300 else self.content
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_published(self):
        return self.status == "published"

    def get_absolute_url(self):
        return reverse("news_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title


class Season(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='seasons/', blank=True, null=True, validators=[image_validator()])
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        indexes = [models.Index(Lower('slug'), name='season_slug_lower_idx')]
        constraints = [
            models.UniqueConstraint(Lower('slug'), name='season_slug_ci_unique')
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.name, max_length=100)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Series(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='series')
    image = models.ImageField(upload_to='series/', blank=True, null=True, validators=[image_validator()])
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Series"
        ordering = ['season', 'order', '-created_at']
        indexes = [
            models.Index(fields=['season', 'order']),
            models.Index(Lower('slug'), name='series_slug_lower_idx'),
        ]
        constraints = [
            models.UniqueConstraint(Lower('slug'), name='series_slug_ci_unique')
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.name, max_length=100)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.season.name} - {self.name}"


class Lesson(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='lessons')
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    featured_image = models.ImageField(upload_to='lessons/', blank=True, null=True, validators=[image_validator()])

    # Content types
    video_url = models.URLField(blank=True, help_text="YouTube or Vimeo URL")
    video_embed_code = models.TextField(blank=True, help_text="Embed code for video")
    pdf_file = models.FileField(upload_to='lessons/pdfs/', blank=True, null=True, validators=[pdf_validator()])
    audio_file = models.FileField(upload_to='lessons/audio/', blank=True, null=True, validators=[audio_validator()])

    # Metadata
    duration_minutes = models.PositiveIntegerField(blank=True, null=True, help_text="Lesson duration in minutes")
    bible_references = models.TextField(blank=True, help_text="Bible verses referenced in this lesson")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    order = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    objects = models.Manager()
    pub = PublishedManager()

    class Meta:
        ordering = ['series', 'order', '-created_at']
        indexes = [
            models.Index(fields=['series', 'status', 'order']),
            models.Index(Lower('slug'), name='lesson_slug_lower_idx'),
        ]
        constraints = [
            models.UniqueConstraint(Lower('slug'), name='lesson_slug_ci_unique')
        ]

    def save(self, *args, **kwargs):
        # detect publish state change to set published_at
        is_update = self.pk is not None
        old_status = None
        if is_update:
            old = Lesson.objects.filter(pk=self.pk).only('status', 'published_at').first()
            old_status = old.status if old else None

        if not self.slug:
            unique_slugify(self, self.title, max_length=200)

        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

        # (signals handle notifications; tunabaki simple hapa)

    def __str__(self):
        return f"{self.series.name} - {self.title}"

    @property
    def like_count(self):
        return self.lesson_likes.count()

    @property
    def comment_count(self):
        return self.lesson_comments.filter(is_approved=True).count()

    @property
    def is_published(self):
        return self.status == "published"

    def get_absolute_url(self):
        # NB: una route mbili: /mafunzo/<slug>/ (page) na /lessons/<slug>/ (pia). Chagua ipi unayotaka.
        return reverse("lesson_detail", kwargs={"slug": self.slug})


class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=200)
    date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    image = models.ImageField(upload_to='events/', blank=True, null=True, validators=[image_validator()])
    registration_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    max_attendees = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']
        indexes = [models.Index(Lower('slug'), name='event_slug_lower_idx')]
        constraints = [
            models.UniqueConstraint(Lower('slug'), name='event_slug_ci_unique')
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.title, max_length=200)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("event_detail", kwargs={"slug": self.slug})


class MediaItem(models.Model):
    MEDIA_TYPES = [
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('image', 'Image'),
        ('document', 'Document'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='media/', blank=True, null=True)
    url = models.URLField(blank=True, help_text="External URL (e.g., YouTube)")
    thumbnail = models.ImageField(upload_to='media/thumbnails/', blank=True, null=True, validators=[image_validator()])
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='media_items', blank=True, null=True)
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class PrayerRequest(models.Model):
    CATEGORY_CHOICES = [
        ('personal', 'Personal'),
        ('family', 'Family'),
        ('health', 'Health'),
        ('work', 'Work'),
        ('spiritual', 'Spiritual'),
        ('community', 'Community'),
        ('other', 'Other'),
    ]
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    request = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)
    is_answered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_urgent', '-created_at']

    def __str__(self):
        if self.is_anonymous:
            return f"Anonymous Prayer Request - {self.get_category_display()}"
        return f"{self.name} - {self.get_category_display()}"


# ---------------- New models for accounts/likes/comments/announcements ----------------

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^[0-9+\-() ]+$', 'Phone number contains invalid characters.')]
    )
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=128, blank=True)
    token_created_at = models.DateTimeField(blank=True, null=True)
    receive_notifications = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile({self.user.username})"


class LessonLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_likes")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="lesson_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'lesson'], name='unique_user_lesson_like')
        ]
        indexes = [models.Index(fields=['lesson', 'user'])]

    def __str__(self):
        return f"{self.user.username} ♥ {self.lesson.slug}"


class LessonComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_comments")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="lesson_comments")
    body = models.TextField()
    is_approved = models.BooleanField(default=True)  # unaweza kubadilisha kuwa moderation ikiwa unataka
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['lesson', 'created_at'])]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.lesson.slug}"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="announcements")

    def __str__(self):
        return self.title
