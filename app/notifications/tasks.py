import logging

from celery import shared_task
from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)


@shared_task
def send_notification_task(notification_id):
    try:
        notification = Notification.objects.get(id=notification_id)

        if notification.status == Notification.Status.SENT:
            logger.info("Notification %s already sent.", notification_id)
            return "Already sent"

        if notification.status == Notification.Status.PERMANENTLY_FAILED:
            logger.info("Notification %s is permanently failed.", notification_id)
            return "Permanently failed"

        if notification.scheduled_time > timezone.now():
            logger.info("Notification %s is not due yet.", notification_id)
            return "Not due yet"

        if "fail" in notification.title.lower():
            raise Exception("Simulated notification failure")

        logger.info(
            "Sending notification %s: %s - %s",
            notification.id,
            notification.title,
            notification.message,
        )

        notification.status = Notification.Status.SENT
        notification.last_error = None
        notification.save(update_fields=["status", "last_error", "updated_at"])

        return "Notification sent"

    except Notification.DoesNotExist:
        logger.error("Notification %s does not exist.", notification_id)
        return "Notification not found"

    except Exception as exc:
        logger.exception("Notification %s failed.", notification_id)

        try:
            notification = Notification.objects.get(id=notification_id)
            notification.retry_count += 1
            notification.last_error = str(exc)

            if notification.retry_count >= 3:
                notification.status = Notification.Status.PERMANENTLY_FAILED
            else:
                notification.status = Notification.Status.FAILED

            notification.save(
                update_fields=[
                    "retry_count",
                    "last_error",
                    "status",
                    "updated_at",
                ]
            )

        except Notification.DoesNotExist:
            logger.error(
                "Notification %s disappeared while handling failure.",
                notification_id,
            )

        return f"Notification failed: {exc}"