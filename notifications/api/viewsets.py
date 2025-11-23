# notifications/api/viewsets.py
from django.apps import apps
from rest_framework import viewsets, permissions, serializers
from typing import Dict, Type

class AdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return True if request.method in ("GET", "HEAD", "OPTIONS") else bool(request.user and request.user.is_staff)

# Cache ili kuzuia duplicate component names kwa Spectacular
_SERIALIZER_CACHE: Dict[type, Type[serializers.ModelSerializer]] = {}

def get_auto_serializer(Model) -> Type[serializers.ModelSerializer]:
    if Model in _SERIALIZER_CACHE:
        return _SERIALIZER_CACHE[Model]
    app = Model._meta.app_label
    name = Model.__name__
    class_name = f"{app}_{name}AutoSerializer"
    ref_name = f"{app}_{name}_Auto"
    Meta = type("Meta", (), {"model": Model, "fields": "__all__", "ref_name": ref_name})
    Cls = type(class_name, (serializers.ModelSerializer,), {"Meta": Meta})
    _SERIALIZER_CACHE[Model] = Cls
    return Cls

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [AdminOrReadOnly]

    def get_model(self):
        return apps.get_model("notifications", "Notification")

    def get_queryset(self):
        Model = self.get_model()
        qs = Model._default_manager.all()
        if hasattr(Model, "is_published") and not getattr(self.request.user, "is_staff", False):
            qs = qs.filter(is_published=True)
        return qs.order_by("-pk")

    def get_serializer_class(self):
        return get_auto_serializer(self.get_model())

__all__ = ["NotificationViewSet"]
