from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "title",
        "scheduled_time",
        "status",
        "retry_count",
        "created_at",
    )
    list_filter = ("status", "scheduled_time", "created_at")
    search_fields = ("title", "message", "user__username")