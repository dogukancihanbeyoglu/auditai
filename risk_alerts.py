"""Explainable risk scoring and bounded alert-management API."""

from flask import Blueprint, jsonify, request

from models import Alarm, AuditRule, DetectionFeedback, RiskScore, db, utcnow
from security import current_user, record_event, require_role
from alarm_review import add_alarm_activity


risk_alerts_bp = Blueprint("risk_alerts", __name__)
SEVERITY_POINTS = {"low": 10, "medium": 25, "high": 50, "critical": 75}
STATUS_MULTIPLIERS = {"open": 1.0, "acknowledged": 0.65, "resolved": 0.15}
MAX_RULES_PER_CALCULATION = 500
MAX_BULK_ALARMS = 100
MAX_EVIDENCE_RECORDS = 100


def _level(score):
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def calculate_rule_risk(rule):
    """Create a deterministic score using persisted evidence only."""
    alarms = list(rule.alarms)
    severity_status_points = round(sum(
        SEVERITY_POINTS.get(alarm.severity, 25) * STATUS_MULTIPLIERS.get(alarm.status, 1.0)
        for alarm in alarms
    ), 2)
    trigger_points = round(min(max(rule.trigger_count, 0), 20) * 1.25, 2)
    failure_points = round(min(max(rule.consecutive_failures, 0), 5) * 5, 2)
    raw_score = severity_status_points + trigger_points + failure_points
    score = round(min(100.0, raw_score), 2)
    components = {
        "severity_status_points": severity_status_points,
        "trigger_points": trigger_points,
        "failure_points": failure_points,
        "raw_score": round(raw_score, 2),
        "capped_at": 100,
    }
    explanation = (
        f"Severity/status evidence contributed {severity_status_points:g} points; "
        f"trigger history contributed {trigger_points:g}; consecutive failures contributed "
        f"{failure_points:g}. Total is capped at 100."
    )
    return RiskScore(
        rule=rule, audit_area=rule.audit_area, score=score, level=_level(score),
        alarm_count=len(alarms), open_alarm_count=sum(alarm.status == "open" for alarm in alarms),
        components=components, explanation=explanation,
    )


def _serialize_score(item):
    return {
        "id": item.id, "rule_id": item.rule_id, "rule_name": item.rule.name,
        "audit_area_id": item.audit_area_id, "audit_area_name": item.audit_area.name,
        "score": item.score, "level": item.level, "alarm_count": item.alarm_count,
        "open_alarm_count": item.open_alarm_count, "components": item.components,
        "explanation": item.explanation, "calculated_at": item.calculated_at.isoformat(),
    }


def _positive_int(value, name):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if parsed < 1 or isinstance(value, bool):
        raise ValueError(f"{name} must be a positive integer")
    return parsed


@risk_alerts_bp.get("/api/risk-scores")
@require_role("auditor")
def list_risk_scores():
    try:
        limit = min(_positive_int(request.args.get("limit", 50), "limit"), 200)
        query = RiskScore.query
        if request.args.get("rule_id"):
            query = query.filter_by(rule_id=_positive_int(request.args["rule_id"], "rule_id"))
        if request.args.get("audit_area_id"):
            query = query.filter_by(audit_area_id=_positive_int(request.args["audit_area_id"], "audit_area_id"))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    scores = query.order_by(RiskScore.calculated_at.desc(), RiskScore.id.desc()).limit(limit).all()
    return jsonify([_serialize_score(item) for item in scores])


@risk_alerts_bp.post("/api/risk-scores/calculate")
@require_role("auditor")
def calculate_risk_scores():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify(error="JSON object required"), 400
    query = AuditRule.query
    if payload.get("audit_area_id") is not None:
        try:
            query = query.filter_by(audit_area_id=_positive_int(payload["audit_area_id"], "audit_area_id"))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
    rules = query.order_by(AuditRule.id).limit(MAX_RULES_PER_CALCULATION + 1).all()
    if len(rules) > MAX_RULES_PER_CALCULATION:
        return jsonify(error=f"calculation is limited to {MAX_RULES_PER_CALCULATION} rules"), 413
    # Relationship reads for later rules must not autoflush earlier, not-yet-added score snapshots.
    with db.session.no_autoflush:
        scores = [calculate_rule_risk(rule) for rule in rules]
    db.session.add_all(scores)
    db.session.flush()
    record_event("risk_scores_calculated", "risk_score", details={"count": len(scores)})
    db.session.commit()
    return jsonify([_serialize_score(item) for item in scores]), 201


@risk_alerts_bp.get("/api/alerts/<int:alarm_id>")
@require_role("auditor")
def alarm_detail(alarm_id):
    alarm = db.get_or_404(Alarm, alarm_id)
    evidence = alarm.affected_records if isinstance(alarm.affected_records, list) else []
    return jsonify({
        "id": alarm.id, "title": alarm.title, "message": alarm.message,
        "severity": alarm.severity, "status": alarm.status,
        "rule": {"id": alarm.rule_id, "name": alarm.rule.name, "type": alarm.rule.rule_type},
        "audit_area": {"id": alarm.audit_area_id, "name": alarm.audit_area.name},
        "data_source": {"id": alarm.data_source_id, "name": alarm.data_source.name},
        "affected_records": evidence[:MAX_EVIDENCE_RECORDS], "affected_record_count": len(evidence),
        "affected_records_truncated": len(evidence) > MAX_EVIDENCE_RECORDS,
        "created_at": alarm.created_at.isoformat(), "updated_at": alarm.updated_at.isoformat(),
    })


@risk_alerts_bp.post("/api/alerts/<int:alarm_id>/feedback")
@require_role("auditor")
def save_detection_feedback(alarm_id):
    alarm = db.get_or_404(Alarm, alarm_id)
    payload = request.get_json(silent=True) or {}
    outcome = payload.get("outcome")
    comment = str(payload.get("comment", "")).strip()
    if outcome not in {"true_positive", "false_positive"} or len(comment) > 2000:
        return jsonify(error="outcome must be true_positive or false_positive; comment max 2000"), 400
    user = current_user()
    feedback = DetectionFeedback.query.filter_by(alarm_id=alarm.id, user_id=user.id).first()
    if not feedback:
        feedback = DetectionFeedback(alarm=alarm, rule=alarm.rule, user=user)
        db.session.add(feedback)
    feedback.outcome = outcome
    feedback.comment = comment
    record_event("detection_feedback_recorded", "alarm", alarm.id, {"outcome": outcome})
    db.session.commit()
    return jsonify(id=feedback.id, alarm_id=alarm.id, rule_id=alarm.rule_id,
                   outcome=feedback.outcome, comment=feedback.comment)


@risk_alerts_bp.get("/api/rules/<int:rule_id>/detection-performance")
@require_role("auditor")
def detection_performance(rule_id):
    rule = db.get_or_404(AuditRule, rule_id)
    feedback = DetectionFeedback.query.filter_by(rule_id=rule.id).all()
    positives = sum(item.outcome == "true_positive" for item in feedback)
    false_positives = sum(item.outcome == "false_positive" for item in feedback)
    reviewed = len(feedback)
    return jsonify(rule_id=rule.id, rule_name=rule.name, reviewed=reviewed,
                   true_positives=positives, false_positives=false_positives,
                   precision=round(positives / reviewed, 4) if reviewed else None,
                   status="measured" if reviewed >= 5 else "insufficient_feedback",
                   minimum_feedback=5)


@risk_alerts_bp.post("/api/alerts/bulk-status")
@require_role("auditor")
def bulk_alarm_status():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="JSON object required"), 400
    alarm_ids = payload.get("alarm_ids")
    action = payload.get("action")
    if not isinstance(alarm_ids, list) or not alarm_ids:
        return jsonify(error="alarm_ids must be a non-empty list"), 400
    if len(alarm_ids) > MAX_BULK_ALARMS:
        return jsonify(error=f"a maximum of {MAX_BULK_ALARMS} alarms is allowed"), 413
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in alarm_ids):
        return jsonify(error="alarm_ids must contain positive integers"), 400
    if len(set(alarm_ids)) != len(alarm_ids):
        return jsonify(error="alarm_ids must be unique"), 400
    target_status = {"acknowledge": "acknowledged", "resolve": "resolved"}.get(action)
    if not target_status:
        return jsonify(error="action must be acknowledge or resolve"), 400
    alarms = Alarm.query.filter(Alarm.id.in_(alarm_ids)).order_by(Alarm.id).all()
    found = {alarm.id for alarm in alarms}
    missing = sorted(set(alarm_ids) - found)
    if missing:
        return jsonify(error="one or more alarms were not found", missing_ids=missing), 404
    invalid = [alarm.id for alarm in alarms if
               (action == "acknowledge" and alarm.status != "open") or
               (action == "resolve" and alarm.status not in {"open", "acknowledged"})]
    if invalid:
        return jsonify(error="invalid alarm status transition", alarm_ids=invalid), 409
    changed_at = utcnow()
    for alarm in alarms:
        previous_status = alarm.status
        alarm.status = target_status
        alarm.updated_at = changed_at
        add_alarm_activity(alarm, "status", from_value=previous_status, to_value=target_status,
                           details={"bulk": True})
    record_event("alarms_bulk_status_changed", "alarm", details={
        "alarm_ids": sorted(alarm_ids), "action": action, "count": len(alarms),
    })
    db.session.commit()
    return jsonify(updated=len(alarms), status=target_status, alarm_ids=sorted(alarm_ids))
