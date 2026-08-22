"""Notification service with a durable in-app outbox and adapter boundary."""

from models import Notification, db


class NotificationService:
    def notify(self, subject, body, *, recipient="auditors", metadata=None):
        notification = Notification(subject=subject, body=body, recipient=recipient,
                                    metadata_json=metadata or {}, status="delivered")
        db.session.add(notification)
        return notification


notification_service = NotificationService()
