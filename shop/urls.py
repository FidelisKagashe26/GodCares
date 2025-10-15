from django.urls import path
from . import views

app_name = "shop"

urlpatterns = [
    path("", views.shop_list, name="list"),
    path("cart/", views.cart_view, name="cart"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("cart/remove/<path:key>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("asante/<int:order_id>/", views.thank_you, name="thank_you"),
    path("<slug:slug>/", views.shop_detail, name="detail"),
]
