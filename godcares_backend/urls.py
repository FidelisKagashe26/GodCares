# godcares_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# ===== Optional: OpenAPI/Swagger/Redoc (drf_spectacular) =====
try:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularSwaggerView,
        SpectacularRedocView,
    )

    _HAS_SPECTACULAR = True
except Exception:
    _HAS_SPECTACULAR = False

# ===== Optional: JWT Auth (simplejwt) =====
try:
    from rest_framework_simplejwt.views import (
        TokenObtainPairView,
        TokenRefreshView,
        TokenVerifyView,
    )

    _HAS_JWT = True
except Exception:
    _HAS_JWT = False

# ===== Optional: shop app check =====
try:
    import shop  # noqa: F401

    _HAS_SHOP = True
except ImportError:
    _HAS_SHOP = False


urlpatterns = [
    # ===== Admin =====
    path("admin/", admin.site.urls),

    # ===== DRF browsable auth =====
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),

    # ===== Versioned REST APIs =====
    # Modular Content API (DRF)
    path(
        "api/v1/content/",
        include(("content.api.urls", "content_api"), namespace="content_api"),
    ),

    # Hizi bado zinatumia urls za kawaida za app zao
    path("api/v1/notifications/", include("notifications.urls")),
    path("api/v1/discipleship/", include("discipleship.urls")),
    path("api/v1/progress/", include("progress.urls")),
    path("api/v1/core/", include("core.urls")),
]

# ===== Shop API (ikiwa app ipo) =====
if _HAS_SHOP:
    urlpatterns += [
        path(
            "api/v1/shop/",
            include(("shop.urls", "shop"), namespace="shop"),
        ),
    ]

# ===== Optional: JWT endpoints =====
if _HAS_JWT:
    urlpatterns += [
        path(
            "api/v1/auth/token/",
            TokenObtainPairView.as_view(),
            name="token_obtain_pair",
        ),
        path(
            "api/v1/auth/token/refresh/",
            TokenRefreshView.as_view(),
            name="token_refresh",
        ),
        path(
            "api/v1/auth/token/verify/",
            TokenVerifyView.as_view(),
            name="token_verify",
        ),
    ]

# ===== Optional: OpenAPI/Swagger/Redoc =====
if _HAS_SPECTACULAR:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/swagger/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/docs/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]

# ===== Static & media (dev only) =====
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ===== Admin branding =====
admin.site.site_header = "GOD CARES 365 Admin"
admin.site.site_title = "GOD CARES 365"
admin.site.index_title = "Content Management"
