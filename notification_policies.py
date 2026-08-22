"""Persistent, non-secret notification routing policies."""

from flask import Blueprint, jsonify, request

from models import Alarm, NotificationPolicy, db
from notifications import notification_service
from security import record_event, require_role


notification_policies_bp = Blueprint("notification_policies", __name__)
SEVERITIES = {"any", "low", "medium", "high", "critical"}
CHANNELS = {"in_app", "email", "webhook"}


def _serialize(policy):
    return {"id": policy.id, "severity": policy.severity, "channel": policy.channel,
            "recipient": policy.recipient, "enabled": policy.enabled,
            "created_at": policy.created_at.isoformat(), "updated_at": policy.updated_at.isoformat()}


def _validate(payload, *, partial=False, policy_id=None):
    if not isinstance(payload, dict):
        return None, "JSON object is required"
    allowed = {"severity", "channel", "recipient", "enabled"}
    if set(payload) - allowed:
        return None, "unknown policy field"
    values = {}
    required = set() if partial else {"severity", "channel", "recipient"}
    if required - set(payload):
        return None, "severity, channel and recipient are required"
    if "severity" in payload:
        severity = str(payload["severity"]).strip().lower()
        if severity not in SEVERITIES:
            return None, "invalid severity"
        values["severity"] = severity
    if "channel" in payload:
        channel = str(payload["channel"]).strip().lower()
        if channel not in CHANNELS:
            return None, "invalid channel"
        values["channel"] = channel
    if "recipient" in payload:
        recipient = str(payload["recipient"]).strip()
        if not recipient or len(recipient) > 255:
            return None, "recipient is required and must not exceed 255 characters"
        values["recipient"] = recipient
    if "enabled" in payload:
        if not isinstance(payload["enabled"], bool):
            return None, "enabled must be a boolean"
        values["enabled"] = payload["enabled"]
    if partial and not values:
        return None, "at least one policy field is required"
    current = db.session.get(NotificationPolicy, policy_id) if policy_id else None
    severity = values.get("severity", current.severity if current else None)
    channel = values.get("channel", current.channel if current else None)
    recipient = values.get("recipient", current.recipient if current else None)
    if channel == "email" and ("@" not in recipient or recipient.startswith("@") or recipient.endswith("@")):
        return None, "email policies require an email recipient"
    if channel == "webhook" and recipient != "configured-webhook":
        return None, "webhook recipient must be configured-webhook; URL and token remain in environment"
    duplicate = NotificationPolicy.query.filter_by(severity=severity, channel=channel, recipient=recipient)
    if policy_id:
        duplicate = duplicate.filter(NotificationPolicy.id != policy_id)
    if duplicate.first():
        return None, "notification policy already exists"
    return values, None


def enqueue_alarm_notifications(alarm: Alarm):
    """Apply enabled routes. Preserve legacy in-app delivery until a policy is configured."""
    policies_exist = NotificationPolicy.query.count() > 0
    policies = NotificationPolicy.query.filter(
        NotificationPolicy.enabled.is_(True),
        NotificationPolicy.severity.in_(("any", alarm.severity)),
    ).order_by(NotificationPolicy.id).all()
    created = []
    for policy in policies:
        item = notification_service.notify(
            f"Audit alert: {alarm.title}", alarm.message, recipient=policy.recipient,
            channels=[policy.channel], metadata={"alarm_id": alarm.id, "severity": alarm.severity,
                                                  "notification_policy_id": policy.id},
        )
        created.append(item)
    if not policies_exist:
        created.append(notification_service.notify(
            f"Audit alert: {alarm.title}", alarm.message,
            metadata={"alarm_id": alarm.id, "severity": alarm.severity},
        ))
    return created


@notification_policies_bp.get("/api/notification-policies")
@require_role("auditor")
def list_policies():
    return jsonify([_serialize(item) for item in NotificationPolicy.query.order_by(
        NotificationPolicy.severity, NotificationPolicy.channel, NotificationPolicy.id).all()])


@notification_policies_bp.post("/api/notification-policies")
@require_role("admin")
def create_policy():
    values, error = _validate(request.get_json(silent=True))
    if error:
        return jsonify(error=error), 409 if "exists" in error else 400
    policy = NotificationPolicy(**values)
    db.session.add(policy)
    db.session.flush()
    record_event("notification_policy_created", "notification_policy", policy.id, values)
    db.session.commit()
    return jsonify(_serialize(policy)), 201


@notification_policies_bp.patch("/api/notification-policies/<int:policy_id>")
@require_role("admin")
def update_policy(policy_id):
    policy = db.get_or_404(NotificationPolicy, policy_id)
    values, error = _validate(request.get_json(silent=True), partial=True, policy_id=policy.id)
    if error:
        return jsonify(error=error), 409 if "exists" in error else 400
    before = {key: getattr(policy, key) for key in values}
    for key, value in values.items():
        setattr(policy, key, value)
    record_event("notification_policy_updated", "notification_policy", policy.id,
                 {"before": before, "after": values})
    db.session.commit()
    return jsonify(_serialize(policy))


@notification_policies_bp.delete("/api/notification-policies/<int:policy_id>")
@require_role("admin")
def delete_policy(policy_id):
    policy = db.get_or_404(NotificationPolicy, policy_id)
    record_event("notification_policy_deleted", "notification_policy", policy.id,
                 {"severity": policy.severity, "channel": policy.channel, "recipient": policy.recipient})
    db.session.delete(policy)
    db.session.commit()
    return "", 204


@notification_policies_bp.post("/api/notification-policies/<int:policy_id>/test")
@require_role("admin")
def test_policy(policy_id):
    policy = db.get_or_404(NotificationPolicy, policy_id)
    item = notification_service.notify("AuditAI notification policy test",
                                       "This is a queued test notification from AuditAI.",
                                       recipient=policy.recipient, channels=[policy.channel],
                                       metadata={"notification_policy_id": policy.id, "test": True})
    db.session.flush()
    record_event("notification_policy_test_queued", "notification_policy", policy.id,
                 {"notification_id": item.id})
    db.session.commit()
    return jsonify(notification_id=item.id, channel=item.channel, recipient=item.recipient,
                   status=item.status), 201
