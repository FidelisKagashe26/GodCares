from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db.models.functions import Lower

# ----------------- Helpers -----------------
def unique_slugify(instance, value, slug_field_name: str = "slug", max_length: int = 200):
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

# ---------------- Existing Models ----------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [models.Index(Lower('slug'), name='category_slug_lower_idx')]
        constraints = [models.UniqueConstraint(Lower('slug'), name='category_slug_ci_unique')]

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.name, max_length=100)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Post(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')]
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
        constraints = [models.UniqueConstraint(Lower('slug'), name='post_slug_ci_unique')]

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
        constraints = [models.UniqueConstraint(Lower('slug'), name='season_slug_ci_unique')]

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
        indexes = [models.Index(fields=['season', 'order']), models.Index(Lower('slug'), name='series_slug_lower_idx')]
        constraints = [models.UniqueConstraint(Lower('slug'), name='series_slug_ci_unique')]

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.name, max_length=100)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.season.name} - {self.name}"

class Lesson(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('published', 'Published'), ('archived', 'Archived')]
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    series = models.ForeignKey(Series, on_delete=models.CASCADE, related_name='lessons')
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)
    featured_image = models.ImageField(upload_to='lessons/', blank=True, null=True, validators=[image_validator()])
    video_url = models.URLField(blank=True, help_text="YouTube or Vimeo URL")
    video_embed_code = models.TextField(blank=True, help_text="Embed code for video")
    pdf_file = models.FileField(upload_to='lessons/pdfs/', blank=True, null=True, validators=[pdf_validator()])
    audio_file = models.FileField(upload_to='lessons/audio/', blank=True, null=True, validators=[audio_validator()])
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
        indexes = [models.Index(fields=['series', 'status', 'order']), models.Index(Lower('slug'), name='lesson_slug_lower_idx')]
        constraints = [models.UniqueConstraint(Lower('slug'), name='lesson_slug_ci_unique')]

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.title, max_length=200)
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def like_count(self):
        return self.lesson_likes.count()

    @property
    def comment_count(self):
        return self.lesson_comments.filter(is_approved=True).count()

    @property
    def is_published(self):
        return self.status == "published"

    def __str__(self):
        return f"{self.series.name} - {self.title}"

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
        constraints = [models.UniqueConstraint(Lower('slug'), name='event_slug_ci_unique')]

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.title, max_length=200)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class MediaItem(models.Model):
    MEDIA_TYPES = [('video', 'Video'), ('audio', 'Audio'), ('image', 'Image'), ('document', 'Document')]
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
    CATEGORY_CHOICES = [('personal', 'Personal'), ('family', 'Family'), ('health', 'Health'), ('work', 'Work'), ('spiritual', 'Spiritual'), ('community', 'Community'), ('other', 'Other')]
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
        if self.is_anonymous: return f"Anonymous Prayer Request - {self.get_category_display()}"
        return f"{self.name} - {self.get_category_display()}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, blank=True, validators=[RegexValidator(r'^[0-9+\-() ]+$', 'Phone number contains invalid characters.')])
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
        constraints = [models.UniqueConstraint(fields=['user', 'lesson'], name='unique_user_lesson_like')]
        indexes = [models.Index(fields=['lesson', 'user'])]

    def __str__(self):
        return f"{self.user.username} ♥ {self.lesson.slug}"

class LessonComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_comments")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="lesson_comments")
    body = models.TextField()
    is_approved = models.BooleanField(default=True)
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

class SiteSetting(models.Model):
    site_name = models.CharField(max_length=120, default="GOD CARES 365")
    tagline = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=200, blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    footer_about = models.TextField(blank=True, default="Tovuti hii imeundwa kukuimarisha katika imani, kukuunga mkono katika maombi, na kukupeleka karibu na Mungu.")
    email_from_name = models.CharField(max_length=120, default="GOD CARES 365")
    email_from_address = models.EmailField(default="fathercares365@gmail.com")
    notifications_opt_in_default = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.pk: self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Site Settings"

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

# ==================== MODELS MPYA ZA GOD CARES 365 MISSION PLATFORM ====================

class DiscipleshipJourney(models.Model):
    STAGE_CHOICES = [
        ('seeker', '📘 Discover Truth - God Cares 365 Student'),
        ('scholar', '📖 Understand Prophecy - God Cares 365 Prophecy Student'), 
        ('missionary', '🌍 Live & Share Message - God Cares 365 Missionary')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='journey')
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='seeker')
    progress_percentage = models.IntegerField(default=0)
    started_date = models.DateTimeField(auto_now_add=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Track progress for each stage
    seeker_completed = models.BooleanField(default=False)
    scholar_completed = models.BooleanField(default=False)
    missionary_completed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Discipleship Journey"
        verbose_name_plural = "Discipleship Journeys"

    def __str__(self):
        return f"{self.user.username} - {self.get_current_stage_display()}"

class StageProgress(models.Model):
    journey = models.ForeignKey(DiscipleshipJourney, on_delete=models.CASCADE, related_name='stage_progress')
    stage = models.CharField(max_length=20, choices=DiscipleshipJourney.STAGE_CHOICES)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='stage_progress')
    completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)  # For quizzes
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['journey', 'lesson']
        verbose_name_plural = "Stage Progress"

    def __str__(self):
        return f"{self.journey.user.username} - {self.lesson.title}"

class MissionReport(models.Model):
    missionary = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mission_reports')
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    gps_coordinates = models.JSONField(default=dict)  # {lat: x, lng: y}
    date_conducted = models.DateTimeField(default=timezone.now)
    souls_reached = models.IntegerField(default=0)
    testimonies = models.TextField(blank=True)
    challenges = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    
    # Baptism records
    baptisms_performed = models.IntegerField(default=0)
    baptism_details = models.JSONField(default=list)  # List of baptism records
    
    # Media evidence
    photos = models.JSONField(default=list)  # List of photo URLs
    videos = models.JSONField(default=list)  # List of video URLs
    
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_missions')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_conducted']

    def __str__(self):
        return f"{self.missionary.username} - {self.location} - {self.date_conducted.strftime('%Y-%m-%d')}"

class BibleStudyGroup(models.Model):
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    ]
    
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_groups')
    group_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(User, related_name='study_groups', blank=True)
    
    # Meeting details
    meeting_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='weekly')
    meeting_schedule = models.JSONField(default=dict)  # {day: "Monday", time: "19:00", frequency: "weekly"}
    location = models.CharField(max_length=200, blank=True)
    online_link = models.URLField(blank=True)
    
    # Group status
    is_active = models.BooleanField(default=True)
    current_members_count = models.IntegerField(default=1)
    max_members = models.IntegerField(default=10)
    
    # Study progress
    current_lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    lessons_completed = models.ManyToManyField(Lesson, related_name='completed_in_groups', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.group_name} - Led by {self.leader.username}"

class BaptismRecord(models.Model):
    missionary = models.ForeignKey(User, on_delete=models.CASCADE, related_name='baptisms_performed')
    candidate_name = models.CharField(max_length=100)
    candidate_age = models.IntegerField(null=True, blank=True)
    candidate_contact = models.CharField(max_length=100, blank=True)
    candidate_email = models.EmailField(blank=True)
    baptism_date = models.DateTimeField()
    location = models.CharField(max_length=100)
    baptism_notes = models.TextField(blank=True)
    
    # Spiritual background
    previous_religion = models.CharField(max_length=100, blank=True)
    testimony = models.TextField(blank=True)
    
    # Follow-up
    follow_up_plan = models.TextField(blank=True)
    follow_up_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-baptism_date']

    def __str__(self):
        return f"{self.candidate_name} - {self.baptism_date.strftime('%Y-%m-%d')}"

class MissionMapLocation(models.Model):
    missionary = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mission_locations')
    location_name = models.CharField(max_length=100)
    gps_coordinates = models.JSONField(default=dict)  # {lat: x, lng: y}
    date_visited = models.DateTimeField()
    visit_type = models.CharField(max_length=50, choices=[
        ('door_to_door', 'Door-to-Door Evangelism'),
        ('bible_study', 'Bible Study Group'),
        ('community', 'Community Outreach'),
        ('follow_up', 'Follow-up Visit'),
        ('baptism', 'Baptism Ceremony')
    ])
    souls_contacted = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    photos = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_visited']

    def __str__(self):
        return f"{self.missionary.username} - {self.location_name} - {self.visit_type}"

class Certificate(models.Model):
    CERTIFICATE_TYPES = [
        ('seeker_completion', '📘 Faith Discovery Badge - Seeker Stage'),
        ('scholar_completion', '📖 Prophetic Insights Award - Scholar Stage'),
        ('missionary_license', '🌍 Certified Missionary License - Missionary Stage'),
        ('bible_study_leader', '👥 Bible Study Group Leader'),
        ('evangelism', '🔥 Evangelism Certificate'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificates')
    certificate_type = models.CharField(max_length=50, choices=CERTIFICATE_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    issued_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Certificate details
    certificate_number = models.CharField(max_length=50, unique=True)
    qr_code = models.ImageField(upload_to='certificates/qr_codes/', blank=True, null=True)
    pdf_certificate = models.FileField(upload_to='certificates/pdfs/', blank=True, null=True)
    
    # Verification
    verified = models.BooleanField(default=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_certificates')
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_date']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class GlobalSoulsCounter(models.Model):
    total_souls_reached = models.BigIntegerField(default=0)
    total_baptisms = models.IntegerField(default=0)
    total_mission_reports = models.IntegerField(default=0)
    total_bible_study_groups = models.IntegerField(default=0)
    active_missionaries = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Global Souls Counter"

    class Meta:
        verbose_name = "Global Souls Counter"
        verbose_name_plural = "Global Souls Counter"