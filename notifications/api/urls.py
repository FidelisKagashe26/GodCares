# notifications/api/urls.py
from rest_framework.routers import DefaultRouter
from .viewsets import NotificationViewSet

router = DefaultRouter()
# register root ('') so that base path /api/v1/notifications/ serves the viewset
router.register(r'', NotificationViewSet, basename='notification')

urlpatterns = router.urls
