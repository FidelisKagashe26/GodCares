# shop/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Category, Product, Order
from .serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    OrderSerializer,
)
from content.permissions import AdminOrReadOnly  # tayari upo kwenye content app


class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD ya Category:
    - Public: GET (list, retrieve)
    - Admin: POST/PUT/PATCH/DELETE
    """
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["slug", "name"]
    search_fields = ["name"]
    ordering_fields = ["name"]
    ordering = ["name"]


class ProductViewSet(viewsets.ModelViewSet):
    """
    Bidhaa + search + featured + related.
    """
    queryset = Product.objects.select_related("category").prefetch_related("gallery")
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "category__slug", "featured", "is_published"]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "price", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(is_published=True)
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """
        GET /products/featured/
        → Orodha ya bidhaa zenye featured=True
        """
        qs = self.get_queryset().filter(featured=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def related(self, request, pk=None):
        """
        GET /products/<id>/related/
        → Bidhaa zinazofanana (category moja)
        """
        product = self.get_object()
        qs = (
            self.get_queryset()
            .filter(category=product.category)
            .exclude(pk=product.pk)[:8]
        )
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    """
    Oda:
    - create: AllowAny (customer aweke oda bila login)
    - list/retrieve/update/delete: Admin pekee.
    """
    queryset = Order.objects.prefetch_related("items__product").all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status", "created_at"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ["create"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
