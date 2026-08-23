"""Read-only reporting and notification API endpoints."""

import csv
import io
import json
import zipfile

from datetime import datetime, timedelta, timezone

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


def _duration_seconds(execution):
    if not execution.finished_at or not execution.started_at:
        return None
    return max(0.0, (execution.finished_at - execution.started_at).total_seconds())


def _priority(severity, open_count):
    if not open_count:
        return "normal"
    return {"critical": "immediate", "high": "high", "medium": "medium"}.get(severity, "low")


def _executive_payload():
    now = datetime.now(timezone.utc)
    try:
        days = min(max(int(request.args.get("days", 30)), 7), 365)
    except ValueError:
        days = 30
    start = _date_arg("from") or now - timedelta(days=days - 1)
    end = _date_arg("to") or now
    area_id = request.args.get("audit_area_id")
    rules_query = AuditRule.query
    if area_id:
        rules_query = rules_query.filter(AuditRule.audit_area_id == area_id)
    rules = rules_query.order_by(AuditRule.name).all()
    executions = _execution_query().filter(RuleExecution.started_at >= start,
                                           RuleExecution.started_at <= end).all()
    alarms = _alarm_query().filter(Alarm.created_at >= start, Alarm.created_at <= end).all()
    execution_by_rule = {rule.id: [] for rule in rules}
    alarm_by_rule = {rule.id: [] for rule in rules}
    for item in executions:
        execution_by_rule.setdefault(item.rule_id, []).append(item)
    for item in alarms:
        alarm_by_rule.setdefault(item.rule_id, []).append(item)

    rule_rows = []
    for rule in rules:
        rule_executions = execution_by_rule.get(rule.id, [])
        rule_alarms = alarm_by_rule.get(rule.id, [])
        durations = [value for item in rule_executions if (value := _duration_seconds(item)) is not None]
        sources = [link.data_source.name for link in rule.source_links] or [rule.data_source.name]
        open_alarms = [item for item in rule_alarms if item.status != "resolved"]
        last_finding = max((item.created_at for item in rule_alarms), default=None)
        scanned = sum(item.scanned_records for item in rule_executions)
        matched = sum(item.matched_records for item in rule_executions)
        rule_rows.append({
            "id": rule.id, "name": rule.name, "audit_area": rule.audit_area.name,
            "rule_type": rule.rule_type, "field_name": rule.field_name,
            "condition": rule.description or f"{rule.field_name} {rule.operator} {rule.threshold_value}",
            "sources": sources, "source_count": len(sources), "severity": rule.severity,
            "is_active": rule.is_active, "schedule_enabled": rule.schedule_enabled,
            "schedule_interval_minutes": rule.schedule_interval_minutes,
            "execution_count": len(rule_executions),
            "successful_executions": sum(item.status == "completed" for item in rule_executions),
            "average_duration_seconds": round(sum(durations) / len(durations), 3) if durations else 0,
            "scanned_records": scanned, "matched_records": matched,
            "match_rate": round(matched / scanned, 4) if scanned else 0,
            "finding_count": len(rule_alarms), "open_findings": len(open_alarms),
            "priority": _priority(rule.severity, len(open_alarms)),
            "last_finding_at": last_finding.isoformat() if last_finding else None,
            "last_run_at": rule.last_run_at.isoformat() if rule.last_run_at else None,
        })

    dates = [(start.date() + timedelta(days=offset))
             for offset in range((end.date() - start.date()).days + 1)]
    trend = [{"date": day.isoformat(),
              "executions": sum(item.started_at.date() == day for item in executions),
              "findings": sum(item.created_at.date() == day for item in alarms),
              "resolved": sum(item.status == "resolved" and item.updated_at.date() == day for item in alarms)}
             for day in dates]
    source_findings = {}
    for alarm in alarms:
        name = alarm.data_source.name
        source_findings[name] = source_findings.get(name, 0) + 1
    severity = {level: sum(item.severity == level for item in alarms)
                for level in ("critical", "high", "medium", "low")}
    status = {level: sum(item.status == level for item in alarms)
              for level in ("open", "acknowledged", "resolved")}
    completed = [item for item in executions if item.status == "completed"]
    durations = [value for item in executions if (value := _duration_seconds(item)) is not None]
    resolved_hours = [max(0.0, (item.updated_at - item.created_at).total_seconds() / 3600)
                      for item in alarms if item.status == "resolved"]
    scanned = sum(item.scanned_records for item in executions)
    matched = sum(item.matched_records for item in executions)
    return {
        "generated_at": now.isoformat(), "period": {"from": start.isoformat(), "to": end.isoformat()},
        "kpis": {"active_rules": sum(rule.is_active for rule in rules),
                 "execution_count": len(executions),
                 "execution_success_rate": round(len(completed) / len(executions), 4) if executions else 0,
                 "scanned_records": scanned, "matched_records": matched,
                 "match_rate": round(matched / scanned, 4) if scanned else 0,
                 "finding_count": len(alarms),
                 "open_findings": sum(item.status != "resolved" for item in alarms),
                 "critical_open_findings": sum(item.status != "resolved" and item.severity == "critical"
                                                for item in alarms),
                 "average_duration_seconds": round(sum(durations) / len(durations), 3) if durations else 0,
                 "average_resolution_hours": round(sum(resolved_hours) / len(resolved_hours), 2)
                 if resolved_hours else 0},
        "findings_by_severity": severity, "findings_by_status": status,
        "findings_by_source": [{"name": name, "count": count} for name, count in
                               sorted(source_findings.items(), key=lambda item: (-item[1], item[0]))],
        "trend": trend, "rules": rule_rows,
    }


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


@reporting_bp.get("/api/reports/executive-dashboard")
@require_role()
def executive_dashboard():
    return jsonify(_executive_payload())


@reporting_bp.get("/api/reports/executive-dashboard.csv")
@require_role("auditor")
def executive_dashboard_csv():
    report = _executive_payload()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Kural", "Denetim alanı", "Kontrol kapsamı", "Veri kaynakları",
                     "Sıklık (dakika)", "Çalıştırma", "Ort. süre (sn)", "Taranan",
                     "Eşleşen", "Bulgu", "Açık bulgu", "Öncelik", "Son bulgu"])
    for rule in report["rules"]:
        writer.writerow([_csv_safe(rule["name"]), _csv_safe(rule["audit_area"]),
                         _csv_safe(rule["condition"]), _csv_safe(", ".join(rule["sources"])),
                         rule["schedule_interval_minutes"] or "Manuel", rule["execution_count"],
                         rule["average_duration_seconds"], rule["scanned_records"],
                         rule["matched_records"], rule["finding_count"], rule["open_findings"],
                         rule["priority"], rule["last_finding_at"] or ""])
    record_event("executive_report_exported", "management_report",
                 details={"format": "csv", "filters": dict(request.args),
                          "rule_count": len(report["rules"])})
    db.session.commit()
    return Response(output.getvalue(), mimetype="text/csv", headers={
        "Content-Disposition": "attachment; filename=auditai-yonetici-raporu.csv",
        "X-Content-Type-Options": "nosniff",
    })


@reporting_bp.get("/api/reports/executive-dashboard.docx")
@require_role("auditor")
def executive_dashboard_docx():
    from services.executive_word_report import build_executive_word_report

    report = _executive_payload()
    document = build_executive_word_report(report)
    record_event("executive_report_exported", "management_report",
                 details={"format": "docx", "filters": dict(request.args),
                          "rule_count": len(report["rules"])})
    db.session.commit()
    return Response(document, mimetype=(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"), headers={
        "Content-Disposition": "attachment; filename=auditai-yonetici-raporu.docx",
        "X-Content-Type-Options": "nosniff",
    })


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
