from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"
        PERMANENTLY_FAILED = "PERMANENTLY_FAILED", "Permanently Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=255)
    message = models.TextField()
    scheduled_time = models.DateTimeField()

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING
    )

    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_retry(self):
        return (
            self.status == self.Status.FAILED
            and self.retry_count < 3
        )

    def __str__(self):
        return f"{self.title} - {self.status}"