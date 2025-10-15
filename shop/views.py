from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Product, Category, Order, OrderItem
from .forms import AddToCartForm, CheckoutForm

def _cart(request):
    return request.session.setdefault("cart", {})

def _cart_key(pid, size, color):
    size = (size or "").strip()
    color = (color or "").strip()
    return f"{pid}:{size}:{color}"

def shop_list(request):
    qs = Product.objects.filter(is_published=True)
    categories = Category.objects.all().order_by("name")

    q = request.GET.get("q", "").strip()
    cat = request.GET.get("cat", "").strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if cat:
        qs = qs.filter(category__slug=cat)

    paginator = Paginator(qs, 12)
    products = paginator.get_page(request.GET.get("page"))

    return render(request, "shop/list.html", {
        "products": products, "categories": categories, "q": q, "cat": cat
    })

def shop_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_published=True)
    related = Product.objects.filter(is_published=True, category=product.category).exclude(pk=product.pk)[:8]

    if request.method == "POST":
        form = AddToCartForm(request.POST)
        if form.is_valid():
            qty = form.cleaned_data["quantity"]
            size = form.cleaned_data.get("size") or ""
            color = form.cleaned_data.get("color") or ""
            if qty > product.inventory:
                messages.error(request, "Samahani, kiasi kilichoombwa kinazidi stock.")
            else:
                cart = _cart(request)
                key = _cart_key(product.id, size, color)
                row = cart.get(key, {"qty": 0})
                row["qty"] = int(row["qty"]) + int(qty)
                row.update({
                    "title": product.title,
                    "slug": product.slug,
                    "price": str(product.price),
                    "image": product.image.url if product.image else "",
                    "size": size, "color": color,
                })
                cart[key] = row
                request.session.modified = True
                messages.success(request, "Imeongezwa kwenye kikapu.")
                return redirect("shop:cart")
    else:
        form = AddToCartForm()

    # toa chaguo la sizes & colors kama list
    sizes = [s.strip() for s in product.sizes.split(",") if s.strip()]
    colors = [c.strip() for c in product.colors.split(",") if c.strip()]

    return render(request, "shop/detail.html", {
        "product": product, "related": related, "form": form,
        "sizes": sizes, "colors": colors
    })

def cart_view(request):
    cart = _cart(request)
    items = []
    total = 0
    for key, row in cart.items():
        qty = int(row["qty"])
        price = float(row["price"])
        line = qty * price
        total += line
        items.append({
            "key": key, "title": row["title"], "slug": row["slug"],
            "qty": qty, "price": price, "line": line,
            "image": row.get("image", ""), "size": row.get("size", ""), "color": row.get("color", "")
        })
    return render(request, "shop/cart.html", {"items": items, "total": total})

def cart_update(request):
    if request.method == "POST":
        cart = _cart(request)
        for key, qty in request.POST.items():
            if key.startswith("qty__"):
                k = key.split("__", 1)[1]
                try:
                    qv = max(0, int(qty))
                except:
                    qv = 1
                if k in cart:
                    if qv == 0:
                        del cart[k]
                    else:
                        cart[k]["qty"] = qv
        request.session.modified = True
    return redirect("shop:cart")

def cart_remove(request, key):
    cart = _cart(request)
    if key in cart:
        del cart[key]
        request.session.modified = True
    return redirect("shop:cart")

def checkout(request):
    cart = _cart(request)
    if not cart:
        messages.info(request, "Kikapu chako kipo tupu.")
        return redirect("shop:list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save()
            # hifadhi vitu
            for key, row in cart.items():
                OrderItem.objects.create(
                    order=order,
                    product=Product.objects.get(pk=int(key.split(":")[0])),
                    quantity=int(row["qty"]),
                    unit_price=row["price"],
                    size=row.get("size", ""), color=row.get("color", "")
                )
            # futa cart
            request.session["cart"] = {}
            request.session.modified = True
            return redirect("shop:thank_you", order_id=order.id)
    else:
        form = CheckoutForm()

    # hesabu total
    items, total = [], 0
    for key, row in cart.items():
        qty = int(row["qty"])
        price = float(row["price"])
        line = qty * price
        total += line
        items.append({**row, "key": key, "qty": qty, "price": price, "line": line})

    return render(request, "shop/checkout.html", {"form": form, "items": items, "total": total})

def thank_you(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "shop/thank_you.html", {"order": order})
