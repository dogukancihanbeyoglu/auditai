"""Read-only reporting and notification API endpoints."""

import csv
import io
import json
import zipfile

from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import func

from models import Alarm, AuditRule, Notification, RiskScore, RuleExecution
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
    for field in ("status", "severity", "rule_id", "audit_area_id", "data_source_id"):
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
    if request.args.get("audit_area_id") or request.args.get("data_source_id"):
        query = query.join(AuditRule)
    if request.args.get("audit_area_id"):
        query = query.filter(AuditRule.audit_area_id == request.args["audit_area_id"])
    if request.args.get("data_source_id"):
        query = query.filter(AuditRule.data_source_id == request.args["data_source_id"])
    if _date_arg("from"):
        query = query.filter(RuleExecution.started_at >= _date_arg("from"))
    if _date_arg("to"):
        query = query.filter(RuleExecution.started_at <= _date_arg("to"))
    return query


def _risk_query():
    query = RiskScore.query
    for field in ("level", "rule_id", "audit_area_id"):
        if request.args.get(field):
            query = query.filter(getattr(RiskScore, field) == request.args[field])
    if _date_arg("from"):
        query = query.filter(RiskScore.calculated_at >= _date_arg("from"))
    if _date_arg("to"):
        query = query.filter(RiskScore.calculated_at <= _date_arg("to"))
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
    risks = _risk_query()
    execution_count = executions.count()
    scanned = executions.with_entities(func.coalesce(func.sum(RuleExecution.scanned_records), 0)).scalar()
    matched = executions.with_entities(func.coalesce(func.sum(RuleExecution.matched_records), 0)).scalar()
    by_status = dict(executions.with_entities(RuleExecution.status, func.count()).group_by(RuleExecution.status).all())
    alarm_by_severity = dict(alarms.with_entities(Alarm.severity, func.count()).group_by(Alarm.severity).all())
    risk_count = risks.count()
    risk_by_level = dict(risks.with_entities(RiskScore.level, func.count()).group_by(RiskScore.level).all())
    average_risk = risks.with_entities(func.coalesce(func.avg(RiskScore.score), 0)).scalar()
    maximum_risk = risks.with_entities(func.coalesce(func.max(RiskScore.score), 0)).scalar()
    return jsonify({"execution_count": execution_count, "scanned_records": scanned,
                    "matched_records": matched, "match_rate": round(matched / scanned, 4) if scanned else 0,
                    "executions_by_status": by_status, "alarm_count": alarms.count(),
                    "alarms_by_severity": alarm_by_severity,
                    "open_alarms": alarms.filter(Alarm.status == "open").count(),
                    "active_rules": AuditRule.query.filter_by(is_active=True).count(),
                    "risk_snapshot_count": risk_count, "risk_by_level": risk_by_level,
                    "average_risk_score": round(float(average_risk), 2),
                    "maximum_risk_score": round(float(maximum_risk), 2)})


@reporting_bp.get("/api/reports/evidence-package.zip")
@require_role("auditor")
def evidence_package():
    alarms = _alarm_query().order_by(Alarm.created_at.desc()).limit(201).all()
    if len(alarms) > 200:
        return jsonify(error="evidence packages are limited to 200 alarms; narrow the filters"), 413
    buffer = io.BytesIO()
    manifest = {"format_version": 1, "filters": dict(request.args), "alarm_count": len(alarms),
                "generated_at": datetime.now(timezone.utc).isoformat()}
    summary = io.StringIO()
    writer = csv.writer(summary)
    writer.writerow(["id", "title", "severity", "status", "rule", "audit_area", "created_at"])
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for alarm in alarms:
            writer.writerow([_csv_safe(alarm.id), _csv_safe(alarm.title), _csv_safe(alarm.severity),
                             _csv_safe(alarm.status), _csv_safe(alarm.rule.name),
                             _csv_safe(alarm.audit_area.name), alarm.created_at.isoformat()])
            evidence = {"alarm_id": alarm.id, "message": alarm.message, "rule_id": alarm.rule_id,
                        "data_source_id": alarm.data_source_id,
                        "affected_records": alarm.affected_records,
                        "created_at": alarm.created_at.isoformat()}
            archive.writestr(f"evidence/alarm-{alarm.id}.json", json.dumps(evidence, ensure_ascii=False, indent=2))
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.writestr("alarms.csv", summary.getvalue())
    record_event("evidence_package_exported", "alarm_report",
                 details={"format": "zip", "filters": dict(request.args), "alarm_count": len(alarms)})
    db.session.commit()
    return Response(buffer.getvalue(), mimetype="application/zip", headers={
        "Content-Disposition": "attachment; filename=auditai-evidence-package.zip",
        "X-Content-Type-Options": "nosniff",
    })


@reporting_bp.get("/api/notifications")
@require_role("auditor")
def notifications():
    items = Notification.query.order_by(Notification.created_at.desc()).limit(100).all()
    return jsonify([{"id": item.id, "channel": item.channel, "recipient": item.recipient,
                     "subject": item.subject, "body": item.body, "status": item.status,
                     "metadata": item.metadata_json, "created_at": item.created_at.isoformat()}
                    for item in items])
