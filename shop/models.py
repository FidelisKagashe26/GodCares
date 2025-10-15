from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self): return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140]
        super().save(*args, **kwargs)


class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    image = models.ImageField(upload_to="shop/products/", blank=True, null=True)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True,
                                           help_text="Bei ya zamani (kuonyesha punguzo).")

    inventory = models.PositiveIntegerField(default=0, help_text="Idadi ya stock ya jumla.")
    sizes = models.CharField(max_length=120, blank=True,
                             help_text="Orodha ya saizi zilizopo, mfano: S,M,L,XL")
    colors = models.CharField(max_length=180, blank=True,
                              help_text="Orodha ya rangi, mfano: Nyeupe, Nyeusi, Bluu")

    featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self): return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200]
            slug = base
            n = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self): return reverse("shop:detail", args=[self.slug])

    @property
    def is_new(self):
        return self.created_at and self.created_at >= timezone.now() - timedelta(days=30)

    @property
    def on_sale(self):
        return bool(self.compare_at_price and self.compare_at_price > self.price)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery")
    image = models.ImageField(upload_to="shop/products/")
    alt = models.CharField(max_length=140, blank=True)

    def __str__(self): return f"{self.product.title} image"


# Checkout nyepesi (bila malipo kwa sasa)
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("cancelled", "Cancelled"),
    ]
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"Order #{self.pk} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=40, blank=True)

    def line_total(self): return self.unit_price * self.quantity
