# shop/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product, ProductImage, Order, OrderItem


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "alt")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "products_count")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = "Products"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "price",
        "inventory",
        "featured",
        "is_published",
        "is_new",
        "on_sale",
        "created_at",
        "thumbnail",
    )
    list_filter = ("is_published", "featured", "category", "created_at")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProductImageInline]
    list_editable = ("featured", "is_published", "price", "inventory")
    readonly_fields = ("created_at",)

    def thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" '
                'style="object-fit:cover;border-radius:6px;" />',
                obj.image.url,
            )
        return "—"
    thumbnail.short_description = "Image"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "unit_price", "size", "color", "line_total_display")
    can_delete = False

    def line_total_display(self, obj):
        return obj.line_total()
    line_total_display.short_description = "Line total"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone", "status", "total_amount_display", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "phone", "email")
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)

    def total_amount_display(self, obj):
        return obj.total_amount
    total_amount_display.short_description = "Total"
