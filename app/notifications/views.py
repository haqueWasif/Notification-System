from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer
from .tasks import send_notification_task


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def perform_create(self, serializer):
        notification = serializer.save(user=self.request.user)

        send_notification_task.apply_async(
            args=[notification.id],
            eta=notification.scheduled_time,
        )

    @action(detail=False, methods=["get"])
    def history(self, request):
        notifications = self.get_queryset()
        serializer = self.get_serializer(notifications, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        notification = self.get_object()

        if notification.status == Notification.Status.SENT:
            return Response(
                {"detail": "Sent notifications cannot be retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if notification.status == Notification.Status.PENDING:
            return Response(
                {"detail": "Pending notifications are already scheduled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if notification.status == Notification.Status.PERMANENTLY_FAILED:
            return Response(
                {"detail": "Permanently failed notifications cannot be retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if notification.retry_count >= 3:
            notification.status = Notification.Status.PERMANENTLY_FAILED
            notification.save(update_fields=["status", "updated_at"])

            return Response(
                {"detail": "Notification has reached the maximum retry limit."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if notification.status != Notification.Status.FAILED:
            return Response(
                {"detail": "Only failed notifications can be retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification.status = Notification.Status.PENDING
        notification.last_error = None
        notification.save(update_fields=["status", "last_error", "updated_at"])

        send_notification_task.apply_async(args=[notification.id])

        serializer = self.get_serializer(notification)

        return Response(
            {
                "detail": "Notification retry has been queued.",
                "notification": serializer.data,
            },
            status=status.HTTP_200_OK,
        )