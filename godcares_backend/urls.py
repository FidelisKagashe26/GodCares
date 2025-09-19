from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from content import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('kuhusu-sisi/', views.about, name='about'),
    path('habari/', views.news, name='news'),
    path('habari/<slug:slug>/', views.news_detail, name='news_detail'),
    path('mafunzo/', views.bible_studies, name='bible_studies'),
    path('mafunzo/<slug:slug>/', views.lesson_detail, name='lesson_detail'),
    path('matukio/', views.events, name='events'),
    path('matukio/<slug:slug>/', views.event_detail, name='event_detail'),
    path('maombi/', views.prayer_requests, name='prayer_requests'),
    path('michango/', views.donations, name='donations'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "GOD CARES 365 Admin"
admin.site.site_title = "GOD CARES 365"
admin.site.index_title = "Content Management"