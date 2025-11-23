# shop/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "shop"

router = DefaultRouter()
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"products", views.ProductViewSet, basename="product")
router.register(r"orders", views.OrderViewSet, basename="order")

urlpatterns = [
    path("api/", include(router.urls)),
]
