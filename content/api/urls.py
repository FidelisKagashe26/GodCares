# content/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import the module, then register classes dynamically (avoid ImportError if missing)
from . import viewsets as vs

router = DefaultRouter()

def maybe_register(prefix: str, cls_name: str, basename: str):
    cls = getattr(vs, cls_name, None)
    if cls is not None:
        router.register(prefix, cls, basename=basename)

maybe_register(r"categories",     "CategoryViewSet",     "category")
maybe_register(r"posts",          "PostViewSet",         "post")
maybe_register(r"series",         "SeriesViewSet",       "series")
maybe_register(r"seasons",        "SeasonViewSet",       "season")
maybe_register(r"lessons",        "LessonViewSet",       "lesson")
maybe_register(r"events",         "EventViewSet",        "event")
maybe_register(r"media-items",    "MediaItemViewSet",    "mediaitem")
maybe_register(r"prayers",        "PrayerRequestViewSet","prayer")

urlpatterns = [
    path("", include(router.urls)),
]
