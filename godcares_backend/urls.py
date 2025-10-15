# godcares_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from content import views
from content.forms import StrictPasswordResetForm
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from core import views as core_views
from core.forms import CustomPasswordChangeForm 

urlpatterns = [
    path('admin/', admin.site.urls),

    path('tafuta/', core_views.site_search, name='site_search'),

    path('account/profile/', core_views.account_profile, name='account_profile'),

    path(
        'account/password/change/',
        auth_views.PasswordChangeView.as_view(
            form_class=CustomPasswordChangeForm,                     # <— TUMIA FORM YETU
            template_name='registration/password_change_form.html',
            success_url=reverse_lazy('password_change_done'),
        ),
        name='password_change'
    ),
    path(
        'account/password/change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='registration/password_change_done.html'
        ),
        name='password_change_done'
    ),

    # Auth basics (login/logout)
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Password reset flow
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.txt',
            html_email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
            form_class=StrictPasswordResetForm,
        ),
        name='password_reset',
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),

    # Pages
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

    # Content app (pages + API under /api/)
    path("", include(("content.urls", "content"), namespace="content")),
    path("duka/", include("shop.urls", namespace="shop")),
    path("", include("notifications.urls")),

    # DRF browsable login (optional)
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

# Serve media/static during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin branding
admin.site.site_header = "GOD CARES 365 Admin"
admin.site.site_title = "GOD CARES 365"
admin.site.index_title = "Content Management"
