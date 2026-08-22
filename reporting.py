"""Read-only reporting and notification API endpoints."""

import csv
import io

from datetime import datetime

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import func

from models import Alarm, AuditRule, Notification, RuleExecution
from models import db
from security import record_event, require_role


reporting_bp = Blueprint("reporting", __name__)


def _csv_safe(value):
    """Prevent spreadsheet applications from evaluating exported cells."""
    text = str(value if value is not None else "")
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text


def _date_arg(name):
    value = request.args.get(name)
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _alarm_query():
    query = Alarm.query
    for field in ("status", "severity", "rule_id", "audit_area_id"):
        if request.args.get(field):
            query = query.filter(getattr(Alarm, field) == request.args[field])
    if _date_arg("from"):
        query = query.filter(Alarm.created_at >= _date_arg("from"))
    if _date_arg("to"):
        query = query.filter(Alarm.created_at <= _date_arg("to"))
    return query


def _execution_query():
    query = RuleExecution.query
    for field in ("status", "trigger", "rule_id"):
        if request.args.get(field):
            query = query.filter(getattr(RuleExecution, field) == request.args[field])
    if _date_arg("from"):
        query = query.filter(RuleExecution.started_at >= _date_arg("from"))
    if _date_arg("to"):
        query = query.filter(RuleExecution.started_at <= _date_arg("to"))
    return query


@reporting_bp.get("/api/reports/alarms.csv")
@require_role("auditor")
def alarms_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "title", "severity", "status", "rule", "audit_area", "created_at"])
    for alarm in _alarm_query().order_by(Alarm.created_at.desc()).all():
        writer.writerow([_csv_safe(alarm.id), _csv_safe(alarm.title), _csv_safe(alarm.severity),
                         _csv_safe(alarm.status), _csv_safe(alarm.rule.name),
                         _csv_safe(alarm.audit_area.name), alarm.created_at.isoformat()])
    record_event("report_exported", "alarm_report", details={"format": "csv", "filters": dict(request.args)})
    db.session.commit()
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=auditai-alarms.csv"})


@reporting_bp.get("/api/reports/alarms")
@require_role()
def alarm_history():
    items = _alarm_query().order_by(Alarm.created_at.desc()).limit(500).all()
    return jsonify([{"id": item.id, "title": item.title, "status": item.status,
                     "severity": item.severity, "rule_id": item.rule_id,
                     "audit_area_id": item.audit_area_id, "created_at": item.created_at.isoformat()}
                    for item in items])


@reporting_bp.get("/api/reports/executions")
@require_role()
def execution_history():
    items = _execution_query().order_by(RuleExecution.started_at.desc()).limit(500).all()
    return jsonify([{"id": item.id, "rule_id": item.rule_id, "rule_name": item.rule.name,
                     "status": item.status, "trigger": item.trigger, "attempt": item.attempt,
                     "scanned_records": item.scanned_records, "matched_records": item.matched_records,
                     "started_at": item.started_at.isoformat(),
                     "finished_at": item.finished_at.isoformat() if item.finished_at else None}
                    for item in items])


@reporting_bp.get("/api/reports/management-summary")
@require_role()
def management_summary():
    executions = _execution_query()
    alarms = _alarm_query()
    execution_count = executions.count()
    scanned = executions.with_entities(func.coalesce(func.sum(RuleExecution.scanned_records), 0)).scalar()
    matched = executions.with_entities(func.coalesce(func.sum(RuleExecution.matched_records), 0)).scalar()
    by_status = dict(executions.with_entities(RuleExecution.status, func.count()).group_by(RuleExecution.status).all())
    alarm_by_severity = dict(alarms.with_entities(Alarm.severity, func.count()).group_by(Alarm.severity).all())
    return jsonify({"execution_count": execution_count, "scanned_records": scanned,
                    "matched_records": matched, "match_rate": round(matched / scanned, 4) if scanned else 0,
                    "executions_by_status": by_status, "alarm_count": alarms.count(),
                    "alarms_by_severity": alarm_by_severity,
                    "open_alarms": alarms.filter(Alarm.status == "open").count(),
                    "active_rules": AuditRule.query.filter_by(is_active=True).count()})


@reporting_bp.get("/api/notifications")
@require_role("auditor")
def notifications():
    items = Notification.query.order_by(Notification.created_at.desc()).limit(100).all()
    return jsonify([{"id": item.id, "channel": item.channel, "recipient": item.recipient,
                     "subject": item.subject, "body": item.body, "status": item.status,
                     "metadata": item.metadata_json, "created_at": item.created_at.isoformat()}
                    for item in items])
