"""Persistent alarm assignment, notes and review timeline API."""

from flask import Blueprint, jsonify, request

from models import Alarm, AlarmActivity, User, db
from security import current_user, record_event, require_role


alarm_review_bp = Blueprint("alarm_review", __name__)


def add_alarm_activity(alarm, event_type, *, from_value=None, to_value=None, note="", details=None):
    actor = current_user()
    activity = AlarmActivity(alarm=alarm, actor_id=actor.id if actor else None, event_type=event_type,
                             from_value=from_value, to_value=to_value, note=note, details=details or {})
    db.session.add(activity)
    return activity


def _serialize(item):
    return {"id": item.id, "event_type": item.event_type, "from_value": item.from_value,
            "to_value": item.to_value, "note": item.note, "details": item.details,
            "actor": ({"id": item.actor.id, "email": item.actor.email} if item.actor else None),
            "created_at": item.created_at.isoformat()}


def _current_assignee(alarm_id):
    item = AlarmActivity.query.filter_by(alarm_id=alarm_id, event_type="assignment").order_by(
        AlarmActivity.created_at.desc(), AlarmActivity.id.desc()).first()
    if not item or not item.to_value:
        return None
    user = db.session.get(User, int(item.to_value))
    return {"id": user.id, "email": user.email, "role": user.role} if user else None


@alarm_review_bp.get("/api/alerts/<int:alarm_id>/review")
@require_role("auditor")
def review_history(alarm_id):
    alarm = db.get_or_404(Alarm, alarm_id)
    items = AlarmActivity.query.filter_by(alarm_id=alarm.id).order_by(
        AlarmActivity.created_at, AlarmActivity.id).all()
    return jsonify(alarm_id=alarm.id, status=alarm.status, assignee=_current_assignee(alarm.id),
                   timeline=[_serialize(item) for item in items])


@alarm_review_bp.post("/api/alerts/<int:alarm_id>/assignment")
@require_role("auditor")
def assign_alarm(alarm_id):
    alarm = db.get_or_404(Alarm, alarm_id)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or set(payload) - {"user_id"}:
        return jsonify(error="JSON object with user_id is required"), 400
    previous = _current_assignee(alarm.id)
    user_id = payload.get("user_id")
    assignee = None
    if user_id is not None:
        if isinstance(user_id, bool) or not isinstance(user_id, int):
            return jsonify(error="user_id must be an integer or null"), 400
        assignee = db.session.get(User, user_id)
        if not assignee or not assignee.is_active or assignee.role not in {"auditor", "admin"}:
            return jsonify(error="assignee must be an active auditor or admin"), 400
    add_alarm_activity(alarm, "assignment", from_value=str(previous["id"]) if previous else None,
                       to_value=str(assignee.id) if assignee else None,
                       details={"assignee_email": assignee.email if assignee else None})
    record_event("alarm_assigned" if assignee else "alarm_unassigned", "alarm", alarm.id,
                 {"user_id": assignee.id if assignee else None})
    db.session.commit()
    return jsonify(alarm_id=alarm.id, assignee=_current_assignee(alarm.id))


@alarm_review_bp.post("/api/alerts/<int:alarm_id>/notes")
@require_role("auditor")
def add_note(alarm_id):
    alarm = db.get_or_404(Alarm, alarm_id)
    payload = request.get_json(silent=True)
    note = str(payload.get("note", "")).strip() if isinstance(payload, dict) else ""
    if not note or len(note) > 4000:
        return jsonify(error="note is required and must not exceed 4000 characters"), 400
    activity = add_alarm_activity(alarm, "note", note=note)
    db.session.flush()
    record_event("alarm_note_added", "alarm", alarm.id, {"activity_id": activity.id})
    db.session.commit()
    return jsonify(_serialize(activity)), 201
