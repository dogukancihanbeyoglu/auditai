"""Durable notification outbox with environment-only delivery adapters."""

from __future__ import annotations

import json
import os
import smtplib
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from models import Notification, db, utcnow


class DeliveryConfigurationError(RuntimeError):
    pass


class EmailAdapter:
    channel = "email"

    def __init__(self, environ=None):
        env = environ or os.environ
        self.host = env.get("SMTP_HOST")
        self.port = int(env.get("SMTP_PORT", "587"))
        self.username = env.get("SMTP_USERNAME")
        self.password = env.get("SMTP_PASSWORD")
        self.sender = env.get("SMTP_FROM")
        self.use_tls = env.get("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}
        if not self.host or not self.sender:
            raise DeliveryConfigurationError("SMTP_HOST and SMTP_FROM are required")

    def deliver(self, notification):
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = self.sender, notification.recipient, notification.subject
        message.set_content(notification.body)
        with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
            if self.use_tls:
                smtp.starttls()
            if self.username:
                smtp.login(self.username, self.password or "")
            smtp.send_message(message)


class WebhookAdapter:
    channel = "webhook"

    def __init__(self, environ=None):
        env = environ or os.environ
        self.url = env.get("NOTIFICATION_WEBHOOK_URL")
        self.token = env.get("NOTIFICATION_WEBHOOK_TOKEN")
        if not self.url:
            raise DeliveryConfigurationError("NOTIFICATION_WEBHOOK_URL is required")

    def deliver(self, notification):
        payload = json.dumps({"subject": notification.subject, "body": notification.body,
                              "metadata": notification.metadata_json}).encode()
        headers = {"Content-Type": "application/json", "User-Agent": "AuditAI/0.1"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(self.url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            if not 200 <= response.status < 300:
                raise RuntimeError(f"webhook returned HTTP {response.status}")


def _parse_timestamp(value):
    return datetime.fromisoformat(value) if value else None


class NotificationService:
    def __init__(self, environ=None):
        self.environ = environ or os.environ

    def notify(self, subject, body, *, recipient="auditors", metadata=None, channels=None):
        configured = channels or [item.strip() for item in self.environ.get("NOTIFICATION_CHANNELS", "in_app").split(",") if item.strip()]
        created = []
        for channel in configured:
            delivered = channel == "in_app"
            target = self.environ.get("NOTIFICATION_EMAIL_TO", recipient) if channel == "email" else recipient
            item = Notification(channel=channel, subject=subject, body=body, recipient=target,
                                metadata_json={**(metadata or {}), "attempts": 0},
                                status="delivered" if delivered else "pending")
            db.session.add(item)
            created.append(item)
        return created[0] if len(created) == 1 else created

    def _adapter(self, channel):
        if channel == "email":
            return EmailAdapter(self.environ)
        if channel == "webhook":
            return WebhookAdapter(self.environ)
        raise DeliveryConfigurationError(f"unsupported delivery channel: {channel}")

    def deliver_due(self, *, now=None, max_attempts=5, base_delay_seconds=60, limit=100):
        now = now or utcnow()
        delivered = retried = failed = 0
        candidates = Notification.query.filter(Notification.status.in_(("pending", "retrying"))).order_by(Notification.id).limit(limit).all()
        for item in candidates:
            metadata = dict(item.metadata_json or {})
            next_attempt = _parse_timestamp(metadata.get("next_attempt_at"))
            if next_attempt and next_attempt > now:
                continue
            attempts = int(metadata.get("attempts", 0)) + 1
            try:
                self._adapter(item.channel).deliver(item)
                item.status = "delivered"
                metadata.update(attempts=attempts, delivered_at=now.isoformat(), last_error=None, next_attempt_at=None)
                delivered += 1
            except Exception as exc:  # adapter failures must remain durable, not escape the worker
                metadata.update(attempts=attempts, last_error=str(exc)[:500])
                if attempts >= max_attempts:
                    item.status = "failed"
                    metadata["next_attempt_at"] = None
                    failed += 1
                else:
                    item.status = "retrying"
                    metadata["next_attempt_at"] = (now + timedelta(seconds=base_delay_seconds * (2 ** (attempts - 1)))).isoformat()
                    retried += 1
            item.metadata_json = metadata
        db.session.commit()
        return {"delivered": delivered, "retrying": retried, "failed": failed}


notification_service = NotificationService()
