from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
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
    featured_image = models.ImageField(upload_to='posts/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'published_at']),
            models.Index(fields=['category', 'status']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.excerpt and self.content:
            self.excerpt = self.content[:297] + '...' if len(self.content) > 300 else self.content
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

class Season(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='seasons/', blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Series(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='series')
    image = models.ImageField(upload_to='series/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Series"
        ordering = ['season', 'order', '-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
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
    featured_image = models.ImageField(upload_to='lessons/', blank=True, null=True)
    
    # Content types
    video_url = models.URLField(blank=True, help_text="YouTube or Vimeo URL")
    video_embed_code = models.TextField(blank=True, help_text="Embed code for video")
    pdf_file = models.FileField(upload_to='lessons/pdfs/', blank=True, null=True)
    audio_file = models.FileField(upload_to='lessons/audio/', blank=True, null=True)
    
    # Metadata
    duration_minutes = models.PositiveIntegerField(blank=True, null=True, help_text="Lesson duration in minutes")
    bible_references = models.TextField(blank=True, help_text="Bible verses referenced in this lesson")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    order = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['series', 'order', '-created_at']
        indexes = [
            models.Index(fields=['series', 'status', 'order']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.series.name} - {self.title}"

class Event(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=200)
    date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    registration_url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    max_attendees = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title

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
    thumbnail = models.ImageField(upload_to='media/thumbnails/', blank=True, null=True)
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