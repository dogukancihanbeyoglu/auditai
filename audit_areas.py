"""Audit Area CRUD API.

Integration: register ``audit_areas_bp`` and remove the legacy list/create routes
from ``app.py``. The blueprint intentionally owns the same canonical URLs.
"""

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from models import AuditArea, db
from security import record_event, require_role


audit_areas_bp = Blueprint("audit_areas", __name__, url_prefix="/api/audit-areas")
MAX_NAME_LENGTH = 128
MAX_DESCRIPTION_LENGTH = 5_000


def serialize_area(area):
    return {
        "id": area.id,
        "name": area.name,
        "description": area.description,
        "is_active": area.is_active,
        "data_source_count": len(area.data_sources),
        "rule_count": len(area.rules),
        "alarm_count": len(area.alarms),
        "created_at": area.created_at.isoformat(),
    }


def _validate(payload, *, partial=False, area_id=None):
    if not isinstance(payload, dict):
        return None, "JSON object is required"
    allowed = {"name", "description", "is_active"}
    unknown = set(payload) - allowed
    if unknown:
        return None, f"unknown field(s): {', '.join(sorted(unknown))}"
    values = {}
    if not partial or "name" in payload:
        name = str(payload.get("name", "")).strip()
        if not name:
            return None, "name is required"
        if len(name) > MAX_NAME_LENGTH:
            return None, f"name must not exceed {MAX_NAME_LENGTH} characters"
        duplicate = AuditArea.query.filter(func.lower(AuditArea.name) == name.lower())
        if area_id is not None:
            duplicate = duplicate.filter(AuditArea.id != area_id)
        if duplicate.first():
            return None, "audit area already exists"
        values["name"] = name
    if "description" in payload or not partial:
        description = str(payload.get("description", "")).strip()
        if len(description) > MAX_DESCRIPTION_LENGTH:
            return None, f"description must not exceed {MAX_DESCRIPTION_LENGTH} characters"
        values["description"] = description
    if "is_active" in payload:
        if not isinstance(payload["is_active"], bool):
            return None, "is_active must be a boolean"
        values["is_active"] = payload["is_active"]
    if partial and not values:
        return None, "at least one editable field is required"
    return values, None


@audit_areas_bp.get("")
@require_role("viewer")
def list_areas():
    query = AuditArea.query
    active = request.args.get("active")
    if active is not None:
        if active.lower() not in {"true", "false"}:
            return jsonify(error="active must be true or false"), 400
        query = query.filter_by(is_active=active.lower() == "true")
    search = request.args.get("q", "").strip()
    if search:
        query = query.filter(AuditArea.name.ilike(f"%{search}%"))
    return jsonify([serialize_area(item) for item in query.order_by(AuditArea.name).all()])


@audit_areas_bp.get("/<int:area_id>")
@require_role("viewer")
def get_area(area_id):
    return jsonify(serialize_area(db.get_or_404(AuditArea, area_id)))


@audit_areas_bp.post("")
@require_role("auditor")
def create_area():
    values, error = _validate(request.get_json(silent=True))
    if error:
        return jsonify(error=error), 409 if "exists" in error else 400
    area = AuditArea(**values)
    db.session.add(area)
    db.session.flush()
    record_event("audit_area_created", "audit_area", area.id,
                 {"name": area.name, "is_active": area.is_active})
    db.session.commit()
    return jsonify(serialize_area(area)), 201


@audit_areas_bp.patch("/<int:area_id>")
@require_role("auditor")
def update_area(area_id):
    area = db.get_or_404(AuditArea, area_id)
    values, error = _validate(request.get_json(silent=True), partial=True, area_id=area.id)
    if error:
        return jsonify(error=error), 409 if "exists" in error else 400
    before = {field: getattr(area, field) for field in values}
    for field, value in values.items():
        setattr(area, field, value)
    record_event("audit_area_updated", "audit_area", area.id, {"before": before, "after": values})
    db.session.commit()
    return jsonify(serialize_area(area))


@audit_areas_bp.post("/<int:area_id>/deactivate")
@require_role("auditor")
def deactivate_area(area_id):
    area = db.get_or_404(AuditArea, area_id)
    changed = area.is_active
    area.is_active = False
    record_event("audit_area_deactivated", "audit_area", area.id, {"changed": changed})
    db.session.commit()
    return jsonify(serialize_area(area))


@audit_areas_bp.delete("/<int:area_id>")
@require_role("admin")
def delete_area(area_id):
    area = db.get_or_404(AuditArea, area_id)
    dependencies = {"data_sources": len(area.data_sources), "rules": len(area.rules), "alarms": len(area.alarms)}
    if any(dependencies.values()):
        return jsonify(error="audit area has linked records; deactivate it instead",
                       dependencies=dependencies, can_deactivate=True), 409
    record_event("audit_area_deleted", "audit_area", area.id, {"name": area.name})
    db.session.delete(area)
    db.session.commit()
    return "", 204
