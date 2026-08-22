"""Audit-safe rule update, activation and deletion endpoints."""

from flask import Blueprint, jsonify, request

from models import AuditArea, AuditRule, DataSource, RuleExecution, db
from security import record_event, require_role
from services.detectors import DetectorError, get_detector
from services.rule_engine import InvalidRule, RULE_TYPES, evaluate_records
from services.compound_rule_engine import CompoundRuleError, validate_compound_rule
from services.scheduler import inspect_schedule


rule_lifecycle_bp = Blueprint("rule_lifecycle", __name__)
SEVERITIES = {"low", "medium", "high", "critical"}
DEFINITION_FIELDS = {"rule_type", "field_name", "parameters", "audit_area_id", "data_source_id"}
ALLOWED_FIELDS = DEFINITION_FIELDS | {"name", "description", "severity"}


def _serialize(rule):
    return {
        "id": rule.id, "name": rule.name, "description": rule.description,
        "rule_type": rule.rule_type, "field_name": rule.field_name,
        "parameters": rule.parameters, "operator": rule.operator,
        "threshold_value": rule.threshold_value, "severity": rule.severity,
        "audit_area_id": rule.audit_area_id, "data_source_id": rule.data_source_id,
        "is_active": rule.is_active, "trigger_count": rule.trigger_count,
        "last_run_at": rule.last_run_at.isoformat() if rule.last_run_at else None,
        "schedule": inspect_schedule(rule),
    }


def _validate_definition(rule_type, field_name, parameters):
    if rule_type == "anomaly":
        detector_name = str(parameters.get("detector", "statistical_zscore"))
        fields = parameters.get("fields") or ([field_name] if field_name else [])
        get_detector(detector_name).detect(
            [], fields=fields, sensitivity=parameters.get("sensitivity", 0.5),
            confidence_threshold=parameters.get("confidence_threshold", 0.8),
            max_evidence=parameters.get("max_evidence", 1000),
        )
        parameters.update(detector=detector_name, fields=list(fields))
    else:
        evaluate_records([], rule_type=rule_type, field=field_name, parameters=parameters)


@rule_lifecycle_bp.get("/api/rules/<int:rule_id>")
@require_role()
def rule_detail(rule_id):
    return jsonify(_serialize(db.get_or_404(AuditRule, rule_id)))


@rule_lifecycle_bp.get("/api/scheduler/status")
@require_role("auditor")
def scheduler_status():
    rules = AuditRule.query.filter(AuditRule.schedule_interval_minutes.isnot(None)).order_by(AuditRule.id).all()
    states = [inspect_schedule(rule) for rule in rules]
    latest = RuleExecution.query.filter_by(trigger="scheduled").order_by(
        RuleExecution.started_at.desc(), RuleExecution.id.desc()).first()
    next_times = [rule.next_run_at for rule in rules
                  if rule.is_active and rule.schedule_enabled and rule.next_run_at]
    return jsonify({
        "configured_rules": len(rules),
        "enabled_rules": sum(state["enabled"] and state["rule_active"] for state in states),
        "due_rules": sum(state["due"] and state["rule_active"] for state in states),
        "locked_rules": sum(state["locked"] for state in states),
        "next_due_at": min(next_times).isoformat() if next_times else None,
        "last_scheduled_execution": ({
            "id": latest.id, "rule_id": latest.rule_id, "status": latest.status,
            "started_at": latest.started_at.isoformat(),
            "finished_at": latest.finished_at.isoformat() if latest.finished_at else None,
        } if latest else None),
    })


@rule_lifecycle_bp.patch("/api/rules/<int:rule_id>")
@require_role("auditor")
def update_rule(rule_id):
    rule = db.get_or_404(AuditRule, rule_id)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload:
        return jsonify(error="non-empty JSON object required"), 400
    unknown = sorted(set(payload) - ALLOWED_FIELDS)
    if unknown:
        return jsonify(error="unsupported fields", fields=unknown), 400
    definition_changed = bool(set(payload) & DEFINITION_FIELDS)
    if definition_changed and (rule.executions or rule.alarms or rule.risk_scores):
        return jsonify(error="executed rule definitions are immutable; create a new rule version"), 409
    name = str(payload.get("name", rule.name)).strip()
    description = str(payload.get("description", rule.description)).strip()
    severity = str(payload.get("severity", rule.severity))
    if not name or len(name) > 128 or len(description) > 5000:
        return jsonify(error="name is required (max 128); description max is 5000"), 400
    if severity not in SEVERITIES:
        return jsonify(error="invalid severity"), 400
    rule_type = str(payload.get("rule_type", rule.rule_type))
    if rule_type not in RULE_TYPES | {"anomaly", "compound"}:
        return jsonify(error="invalid rule type"), 400
    field_name = str(payload.get("field_name", rule.field_name)).strip()
    parameters = dict(payload.get("parameters", rule.parameters) or {})
    if definition_changed:
        try:
            if rule_type == "compound":
                parameters = validate_compound_rule(parameters)
            else:
                _validate_definition(rule_type, field_name, parameters)
        except (InvalidRule, DetectorError, CompoundRuleError, TypeError, ValueError) as exc:
            return jsonify(error=str(exc)), 400
    area_id = payload.get("audit_area_id", rule.audit_area_id)
    source_id = payload.get("data_source_id", rule.data_source_id)
    try:
        area_id, source_id = int(area_id), int(source_id)
    except (TypeError, ValueError):
        return jsonify(error="audit_area_id and data_source_id must be integers"), 400
    source = db.session.get(DataSource, source_id)
    if not db.session.get(AuditArea, area_id) or not source or source.audit_area_id != area_id:
        return jsonify(error="invalid audit area or data source"), 400
    rule.name, rule.description, rule.severity = name, description, severity
    rule.rule_type, rule.field_name, rule.parameters = rule_type, field_name, parameters
    rule.audit_area_id, rule.data_source_id = area_id, source_id
    if rule_type == "numeric":
        rule.operator = str(parameters.get("operator", "=="))
        rule.threshold_value = float(parameters["value"])
    record_event("rule_updated", "audit_rule", rule.id, {"fields": sorted(payload)})
    db.session.commit()
    return jsonify(_serialize(rule))


@rule_lifecycle_bp.patch("/api/rules/<int:rule_id>/active")
@require_role("auditor")
def set_rule_active(rule_id):
    rule = db.get_or_404(AuditRule, rule_id)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("is_active"), bool):
        return jsonify(error="is_active must be a boolean"), 400
    active = payload["is_active"]
    if rule.is_active == active:
        return jsonify(_serialize(rule))
    rule.is_active = active
    if not active:
        rule.schedule_enabled = False
        rule.execution_lock_token = None
        rule.execution_lock_until = None
    record_event("rule_enabled" if active else "rule_disabled", "audit_rule", rule.id)
    db.session.commit()
    return jsonify(_serialize(rule))


@rule_lifecycle_bp.delete("/api/rules/<int:rule_id>")
@require_role("auditor")
def delete_rule(rule_id):
    rule = db.get_or_404(AuditRule, rule_id)
    dependencies = {"executions": len(rule.executions), "alarms": len(rule.alarms),
                    "risk_scores": len(rule.risk_scores)}
    if any(dependencies.values()):
        return jsonify(error="rule has audit evidence and cannot be deleted; disable it instead",
                       dependencies=dependencies), 409
    record_event("rule_deleted", "audit_rule", rule.id, {"name": rule.name})
    db.session.delete(rule)
    db.session.commit()
    return "", 204
