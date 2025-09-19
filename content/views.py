from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import (
    Category, Post, Season, Series, Lesson, 
    Event, MediaItem, PrayerRequest
)
from .forms import PrayerRequestForm

def home(request):
    """Home page view"""
    featured_posts = Post.objects.filter(status='published', featured=True)[:3]
    upcoming_events = Event.objects.filter(date__gte=timezone.now())[:3]
    
    context = {
        'featured_posts': featured_posts,
        'upcoming_events': upcoming_events,
        'current_year': timezone.now().year,
    }
    return render(request, 'home.html', context)

def about(request):
    """About page view"""
    return render(request, 'about.html')

def news(request):
    """News listing page"""
    posts = Post.objects.filter(status='published').select_related('category', 'author')
    categories = Category.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query)
        )
    
    # Category filtering
    category_filter = request.GET.get('category', '')
    if category_filter and category_filter != 'all':
        posts = posts.filter(category__slug=category_filter)
    
    # Pagination
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
    }
    return render(request, 'news/list.html', context)

def news_detail(request, slug):
    """News detail page"""
    post = get_object_or_404(Post, slug=slug, status='published')
    
    # Increment view count
    post.views += 1
    post.save(update_fields=['views'])
    
    # Get related posts
    related_posts = Post.objects.filter(
        category=post.category, 
        status='published'
    ).exclude(id=post.id)[:3]
    
    context = {
        'post': post,
        'related_posts': related_posts,
    }
    return render(request, 'news/detail.html', context)

def bible_studies(request):
    """Bible studies page"""
    seasons = Season.objects.filter(is_active=True).prefetch_related('series__lessons')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    lessons = Lesson.objects.filter(status='published').select_related('series', 'series__season')
    
    if search_query:
        lessons = lessons.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(bible_references__icontains=search_query)
        )
    
    # Season filtering
    season_filter = request.GET.get('season', '')
    if season_filter and season_filter != 'all':
        lessons = lessons.filter(series__season__slug=season_filter)
    
    # Pagination for lessons
    paginator = Paginator(lessons, 9)
    page_number = request.GET.get('page')
    lessons_page = paginator.get_page(page_number)
    
    context = {
        'seasons': seasons,
        'lessons_page': lessons_page,
        'search_query': search_query,
        'season_filter': season_filter,
    }
    return render(request, 'bible_studies/list.html', context)

def lesson_detail(request, slug):
    """Lesson detail page"""
    lesson = get_object_or_404(Lesson, slug=slug, status='published')
    
    # Increment view count
    lesson.views += 1
    lesson.save(update_fields=['views'])
    
    # Get other lessons in the same series
    related_lessons = Lesson.objects.filter(
        series=lesson.series,
        status='published'
    ).exclude(id=lesson.id).order_by('order')[:5]
    
    context = {
        'lesson': lesson,
        'related_lessons': related_lessons,
    }
    return render(request, 'bible_studies/detail.html', context)

def events(request):
    """Events listing page"""
    all_events = Event.objects.all().order_by('date')
    
    # Filter by type
    event_filter = request.GET.get('filter', 'all')
    if event_filter == 'upcoming':
        events_list = all_events.filter(date__gte=timezone.now())
    elif event_filter == 'featured':
        events_list = all_events.filter(is_featured=True)
    else:
        events_list = all_events
    
    # Pagination
    paginator = Paginator(events_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'event_filter': event_filter,
    }
    return render(request, 'events/list.html', context)

def event_detail(request, slug):
    """Event detail page"""
    event = get_object_or_404(Event, slug=slug)
    
    context = {
        'event': event,
    }
    return render(request, 'events/detail.html', context)

def prayer_requests(request):
    """Prayer requests page"""
    if request.method == 'POST':
        form = PrayerRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ombi lako limepokewa! Timu yetu itaomba kwa ajili yako.')
            return redirect('prayer_requests')
    else:
        form = PrayerRequestForm()
    
    context = {
        'form': form,
    }
    return render(request, 'prayer_requests.html', context)

def donations(request):
    """Donations page"""
    return render(request, 'donations.html')