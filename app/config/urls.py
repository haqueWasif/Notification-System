from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


def api_home(request):
    return JsonResponse({
        "message": "Notification API is running",
        "routes": {
            "health_check": "/api/health/",
            "register": "/api/auth/register/",
            "login": "/api/auth/token/",
            "refresh_token": "/api/auth/token/refresh/",
            "notifications": "/api/notifications/",
            "notification_history": "/api/notifications/history/",
            "retry_failed_notification": "/api/notifications/{id}/retry/",
            "admin": "/admin/"
        },
        "note": "Protected routes require JWT Bearer token authentication."
    })


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "message": "Notification API is running"
    })


urlpatterns = [
    path("", api_home, name="api-home"),
    path("api/health/", health_check, name="api-health"),

    path("admin/", admin.site.urls),

    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("api/auth/", include("accounts.urls")),
    path("api/notifications/", include("notifications.urls")),
]