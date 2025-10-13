# notifications/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("notifications/", views.inbox, name="notifications_inbox"),
    path("notifications/open/<int:pk>/", views.open_and_redirect, name="notifications_open"),
    path("notifications/unread-count/", views.unread_count, name="notifications_unread_count"),
    path("notifications/mark-all-read/", views.mark_all_read, name="notifications_mark_all_read"),
    path("notifications/broadcast/", views.broadcast, name="notifications_broadcast"),

    path("api/notifications/unread-count/", views.api_unread_count, name="api_unread_count"),
    path("api/notifications/mark-read/<int:pk>/", views.api_mark_read, name="api_mark_read"),
    path("api/notifications/mark-all-read/", views.api_mark_all_read, name="api_mark_all_read"),
]
