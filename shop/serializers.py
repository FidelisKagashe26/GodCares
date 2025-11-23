# shop/serializers.py
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Category, Product, ProductImage, Order, OrderItem


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Picha za ziada (gallery) za bidhaa.
    """

    class Meta:
        model = ProductImage
        fields = ["id", "image", "alt"]


class CategorySerializer(serializers.ModelSerializer):
    """
    Category za duka (shop).
    Tunatumia ref_name ili kuepuka clash na CategorySerializer ya content.api.
    """

    products_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "products_count"]
        ref_name = "ShopCategory"

    def get_products_count(self, obj) -> int:
        return obj.products.filter(is_published=True).count()


class ProductListSerializer(serializers.ModelSerializer):
    """
    List view ya bidhaa (grid/list kwenye shop).
    """

    category = CategorySerializer(read_only=True)
    is_new = serializers.BooleanField(read_only=True)
    on_sale = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "image",
            "price",
            "compare_at_price",
            "inventory",
            "featured",
            "is_published",
            "is_new",
            "on_sale",
            "created_at",
        ]
        ref_name = "ShopProductList"


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Detail view ya bidhaa moja (product page).
    """

    category = CategorySerializer(read_only=True)
    gallery = ProductImageSerializer(many=True, read_only=True)
    is_new = serializers.BooleanField(read_only=True)
    on_sale = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "slug",
            "category",
            "image",
            "gallery",
            "description",
            "price",
            "compare_at_price",
            "inventory",
            "sizes",
            "colors",
            "featured",
            "is_published",
            "is_new",
            "on_sale",
            "created_at",
        ]
        ref_name = "ShopProductDetail"


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Item moja ndani ya Order (nested).
    """

    product_title = serializers.CharField(source="product.title", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_image = serializers.ImageField(source="product.image", read_only=True)
    line_total = serializers.SerializerMethodField()

    # product lazima iwe kwenye products zilizo published
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_published=True)
    )

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "product_title",
            "product_slug",
            "product_image",
            "quantity",
            "unit_price",
            "size",
            "color",
            "line_total",
        ]
        # unit_price haiji kutoka kwa client, tunai-set sisi kutoka kwenye Product
        read_only_fields = ["unit_price"]
        ref_name = "ShopOrderItem"

    def get_line_total(self, obj) -> Decimal:
        return obj.unit_price * obj.quantity


class OrderSerializer(serializers.ModelSerializer):
    """
    Order (checkout) na items zake zote.
    - items: nested write (tunajenga Order + OrderItems)
    - total_amount: inahesabiwa kutoka kwa items, sio input ya client
    """

    items = OrderItemSerializer(many=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "full_name",
            "phone",
            "email",
            "address",
            "notes",
            "status",
            "created_at",
            "items",
            "total_amount",
        ]
        read_only_fields = ["status", "created_at"]
        ref_name = "ShopOrder"

    def get_total_amount(self, obj) -> Decimal:
        """
        Jumla ya order = sum(unit_price * quantity) kwa kila item.
        """
        total = Decimal("0.00")
        for item in obj.items.all():
            total += item.unit_price * item.quantity
        return total

    @transaction.atomic
    def create(self, validated_data):
        """
        Tengeneza Order + OrderItems, ukihakikisha:
        - Angalau item 1 ipo
        - Stock inatosha
        - Inventory inapungua salama kupitia F()
        """
        items_data = validated_data.pop("items", [])

        if not items_data:
            raise ValidationError(
                {"items": "Angalau bidhaa moja inahitajika kwenye oda."}
            )

        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            product = item_data["product"]
            quantity = item_data.get("quantity") or 1
            size = item_data.get("size", "") or ""
            color = item_data.get("color", "") or ""

            if quantity <= 0:
                raise ValidationError(
                    {"quantity": "Quantity lazima iwe 1 au zaidi."}
                )

            # hakikisha stock inatosha
            product.refresh_from_db()
            if product.inventory < quantity:
                raise ValidationError(
                    {"inventory": f"Stock haitoshi kwa bidhaa: {product.title}."}
                )

            # unit_price tunachukua kutoka kwenye product, sio kutoka kwa client
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
                size=size,
                color=color,
            )

            # punguza inventory salama
            Product.objects.filter(pk=product.pk).update(
                inventory=F("inventory") - quantity
            )

        return order
