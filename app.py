"""AuditAI: a functional audit-rule and alert-management prototype."""

import os
import secrets
from datetime import timedelta
from pathlib import Path

import click
from flask import Flask, jsonify, render_template, request

from config import build_runtime_config
from csrf import init_csrf
from alarm_review import add_alarm_activity, alarm_review_bp
from migration_support import migrate
from models import (Alarm, AuditArea, AuditEvent, AuditRule, DataSource, QualityCheck,
                    QualityCheckRun, RiskScore, RuleExecution, User, db, utcnow)
from notification_policies import notification_policies_bp
from reporting import reporting_bp
from postgres_routes import postgres_bp
from security import hash_password, record_event, require_role, security_bp
from services.execution import run_rule as execute_rule
from services.rule_engine import InvalidRule, RULE_TYPES, evaluate_records
from services.scheduler import disable_schedule, inspect_schedule, resume_schedule, run_due_rules
from ops.readiness import readiness_report
from audit_areas import audit_areas_bp
from data_governance import data_governance_bp
from risk_alerts import risk_alerts_bp
from source_sync import source_sync_bp
from services.detectors import DetectorError, get_detector
from rule_lifecycle import rule_lifecycle_bp
from compound_rules import compound_rules_bp


SEVERITIES = {"low", "medium", "high", "critical"}
STATUSES = {"open", "acknowledged", "resolved"}


def serialize_area(area):
    return {"id": area.id, "name": area.name, "description": area.description, "is_active": area.is_active}


def serialize_source(source):
    records = source.config.get("records", []) if source.config else []
    return {"id": source.id, "name": source.name, "source_type": source.source_type,
            "audit_area_id": source.audit_area_id, "audit_area_name": source.audit_area.name,
            "record_count": len(records), "is_active": source.is_active,
            "last_sync": source.last_sync.isoformat() if source.last_sync else None,
            "mapping_count": len(source.field_mappings),
            "quality_check_count": len(source.quality_checks)}


def serialize_rule(rule):
    return {"id": rule.id, "name": rule.name, "description": rule.description,
            "field_name": rule.field_name, "operator": rule.operator,
            "threshold_value": rule.threshold_value, "severity": rule.severity,
            "rule_type": rule.rule_type, "parameters": rule.parameters,
            "schedule_interval_minutes": rule.schedule_interval_minutes,
            "schedule_enabled": rule.schedule_enabled,
            "next_run_at": rule.next_run_at.isoformat() if rule.next_run_at else None,
            "is_active": rule.is_active, "trigger_count": rule.trigger_count,
            "audit_area_id": rule.audit_area_id, "data_source_id": rule.data_source_id,
            "last_run_at": rule.last_run_at.isoformat() if rule.last_run_at else None,
            "schedule": inspect_schedule(rule),
            "source_links": [{"id": link.id, "data_source_id": link.data_source_id,
                              "data_source_name": link.data_source.name, "alias": link.alias,
                              "priority": link.priority, "join_to_alias": link.join_to_alias,
                              "left_field": link.left_field, "right_field": link.right_field,
                              "join_type": link.join_type, "join_operator": link.join_operator}
                             for link in rule.source_links]}


def serialize_alarm(alarm):
    return {"id": alarm.id, "title": alarm.title, "message": alarm.message,
            "severity": alarm.severity, "status": alarm.status,
            "affected_records": alarm.affected_records, "rule_id": alarm.rule_id,
            "rule_name": alarm.rule.name, "audit_area_name": alarm.audit_area.name,
            "created_at": alarm.created_at.isoformat()}


def seed_demo_data():
    if AuditArea.query.first():
        return
    area = AuditArea(name="Procure-to-Pay", description="Vendor payments and purchasing controls")
    source = DataSource(name="Synthetic invoice ledger", audit_area=area, config={"records": [
        {"id": "INV-1001", "vendor": "Atlas Office", "amount": 1450, "duplicate_count": 1},
        {"id": "INV-1002", "vendor": "Northwind Consulting", "amount": 27500, "duplicate_count": 1},
        {"id": "INV-1003", "vendor": "Atlas Office", "amount": 1450, "duplicate_count": 2},
        {"id": "INV-1004", "vendor": "Contoso Logistics", "amount": 62000, "duplicate_count": 1},
    ]})
    db.session.add_all([
        area,
        AuditRule(name="High-value invoice", description="Flags invoices above the approval threshold",
                  field_name="amount", operator=">", threshold_value=25000, severity="high",
                  audit_area=area, data_source=source),
        AuditRule(name="Potential duplicate", description="Flags repeated invoice indicators",
                  field_name="duplicate_count", operator=">", threshold_value=1, severity="critical",
                  audit_area=area, data_source=source),
    ])
    db.session.commit()


def create_app(test_config=None):
    app = Flask(__name__)
    default_db = Path(app.instance_path) / "auditai.db"
    runtime_config = build_runtime_config(os.environ, default_db)
    app.config.update(SQLALCHEMY_DATABASE_URI=runtime_config["SQLALCHEMY_DATABASE_URI"],
                      SQLALCHEMY_TRACK_MODIFICATIONS=False, JSON_SORT_KEYS=False,
                      SECRET_KEY=runtime_config["SECRET_KEY"] or secrets.token_hex(32),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                      SESSION_COOKIE_SECURE=runtime_config["SESSION_COOKIE_SECURE"],
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=8), AUTH_REQUIRED=True,
                      AUDITAI_ENV=runtime_config["AUDITAI_ENV"],
                      AUTO_CREATE_SCHEMA=runtime_config["AUTO_CREATE_SCHEMA"],
                      EVIDENCE_SAMPLE_LIMIT=int(os.environ.get("EVIDENCE_SAMPLE_LIMIT", "1000")))
    if test_config:
        app.config.update(test_config)
    init_csrf(app)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"))
    app.register_blueprint(security_bp)
    app.register_blueprint(reporting_bp)
    app.register_blueprint(postgres_bp)
    app.register_blueprint(audit_areas_bp)
    app.register_blueprint(data_governance_bp)
    app.register_blueprint(risk_alerts_bp)
    app.register_blueprint(alarm_review_bp)
    app.register_blueprint(notification_policies_bp)
    app.register_blueprint(source_sync_bp)
    app.register_blueprint(rule_lifecycle_bp)
    app.register_blueprint(compound_rules_bp)

    @app.cli.command("create-admin")
    @click.option("--email", prompt=True)
    @click.password_option(confirmation_prompt=True)
    def create_admin(email, password):
        """Create the initial local administrator without exposing credentials in logs."""
        normalized_email = email.strip().lower()
        if "@" not in normalized_email:
            raise click.ClickException("a valid email is required")
        if User.query.filter_by(email=normalized_email).first():
            raise click.ClickException("user already exists")
        try:
            password_hash = hash_password(password)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        db.session.add(User(email=normalized_email, password_hash=password_hash, role="admin"))
        db.session.commit()
        click.echo("Administrator created.")

    @app.cli.command("run-scheduled")
    def run_scheduled():
        """Run due controls once; invoke from cron or a worker."""
        executions = run_due_rules()
        click.echo(f"Processed {len(executions)} scheduled control(s).")
    from data_sources import data_sources_bp
    app.register_blueprint(data_sources_bp)

    @app.get("/")
    @require_role()
    def index():
        return render_template("workspace.html", page="dashboard")

    @app.get("/<page_name>")
    @require_role()
    def workspace_page(page_name):
        pages = {"audit-areas", "data-sources", "data-governance", "rules",
                 "executions", "alerts", "risk-scores", "reports",
                 "notifications", "audit-logs", "system-health", "settings"}
        if page_name not in pages:
            return jsonify(error="page not found"), 404
        return render_template("workspace.html", page=page_name)

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="auditai")

    @app.get("/ready")
    def ready():
        payload, status = readiness_report()
        return jsonify(payload), status

    @app.get("/api/summary")
    @require_role()
    def summary():
        return jsonify(audit_areas=AuditArea.query.count(), data_sources=DataSource.query.count(),
                       active_rules=AuditRule.query.filter_by(is_active=True).count(),
                       open_alarms=Alarm.query.filter_by(status="open").count())

    @app.get("/api/dashboard/insights")
    @require_role()
    def dashboard_insights():
        now = utcnow()
        alarms = Alarm.query.all()
        sources = DataSource.query.all()
        rules = AuditRule.query.all()
        executions = RuleExecution.query.all()
        resolved = [item for item in alarms if item.status == "resolved"]
        daily, execution_daily = [], []
        for offset in range(13, -1, -1):
            day = (now - timedelta(days=offset)).date()
            daily.append({"date": day.isoformat(), "count": sum(
                1 for item in alarms if item.created_at and item.created_at.date() == day)})
            day_executions = [item for item in executions
                              if item.started_at and item.started_at.date() == day]
            execution_daily.append({"date": day.isoformat(), "total": len(day_executions),
                                    "failed": sum(1 for item in day_executions
                                                  if item.status == "failed")})
        source_types = {}
        for source in sources:
            source_types[source.source_type] = source_types.get(source.source_type, 0) + 1
        areas = []
        for area in AuditArea.query.all():
            areas.append({"id": area.id, "name": area.name, "alarm_count": len(area.alarms),
                          "rule_count": len(area.rules)})
        areas.sort(key=lambda item: (-item["alarm_count"], item["name"].lower()))
        recent_events = AuditEvent.query.order_by(AuditEvent.created_at.desc()).limit(5).all()
        ai_rules = AuditRule.query.filter_by(rule_type="anomaly", is_active=True).count()
        completed_executions = sum(1 for item in executions if item.status == "completed")
        failed_executions = sum(1 for item in executions if item.status == "failed")
        total_records = sum(len((source.config or {}).get("records", [])) for source in sources)
        severity_breakdown = {severity: sum(1 for item in alarms if item.severity == severity)
                              for severity in ("critical", "high", "medium", "low")}
        status_breakdown = {status: sum(1 for item in alarms if item.status == status)
                            for status in ("open", "acknowledged", "resolved")}
        quality_latest = []
        for check in QualityCheck.query.filter_by(is_active=True).all():
            run = QualityCheckRun.query.filter_by(quality_check_id=check.id).order_by(
                QualityCheckRun.started_at.desc()).first()
            quality_latest.append(run.status if run else "not_run")
        quality_breakdown = {status: quality_latest.count(status)
                             for status in ("passed", "failed", "not_run")}
        latest_risks = {}
        for risk in RiskScore.query.order_by(RiskScore.calculated_at.desc()).all():
            latest_risks.setdefault(risk.rule_id, risk)
        risk_breakdown = {level: sum(1 for risk in latest_risks.values() if risk.level == level)
                          for level in ("critical", "high", "medium", "low")}
        due_schedules = sum(1 for rule in rules if rule.is_active and inspect_schedule(rule)["due"])
        active_sources = sum(1 for source in sources if source.is_active)
        open_critical = sum(1 for item in alarms
                            if item.status == "open" and item.severity == "critical")
        actions = [
            {"label": "Kritik alarmları incele", "count": open_critical, "href": "/alerts",
             "level": "critical", "description": "Acil değerlendirme bekleyen kritik bulgular"},
            {"label": "Başarısız çalıştırmaları çöz", "count": failed_executions,
             "href": "/executions", "level": "high",
             "description": "Teknik hata ile tamamlanamayan kontrol çalıştırmaları"},
            {"label": "Veri kalitesi sorunlarını incele", "count": quality_breakdown["failed"],
             "href": "/data-governance", "level": "medium",
             "description": "Son kalite sonucu başarısız olan kontroller"},
            {"label": "Pasif kaynakları etkinleştir", "count": len(sources) - active_sources,
             "href": "/data-sources", "level": "medium",
             "description": "Şu anda izleme kapsamı dışında kalan kaynaklar"},
            {"label": "Bekleyen zamanlanmış kontroller", "count": due_schedules,
             "href": "/rules", "level": "low",
             "description": "Çalışma zamanı gelmiş otomatik kontroller"},
        ]
        return jsonify(
            generated_at=now.isoformat(), total_records=total_records,
            critical_alarms=open_critical,
            resolved_today=sum(1 for item in resolved if item.updated_at and item.updated_at.date() == now.date()),
            resolution_rate=round((len(resolved) / len(alarms) * 100), 1) if alarms else 100.0,
            anomaly_rules=ai_rules, daily_alarms=daily, source_types=source_types,
            execution_daily=execution_daily,
            execution_summary={"total": len(executions), "completed": completed_executions,
                               "failed": failed_executions,
                               "success_rate": round(completed_executions / len(executions) * 100, 1)
                               if executions else 100.0},
            source_summary={"total": len(sources), "active": active_sources,
                            "inactive": len(sources) - active_sources,
                            "coverage_rate": round(active_sources / len(sources) * 100, 1)
                            if sources else 100.0},
            alarm_severity=severity_breakdown, alarm_status=status_breakdown,
            quality_summary=quality_breakdown, risk_summary=risk_breakdown,
            action_queue=actions,
            top_areas=areas[:5], recent_events=[{
                "id": item.id, "action": item.action, "entity_type": item.entity_type,
                "entity_id": item.entity_id, "created_at": item.created_at.isoformat()
            } for item in recent_events])

    @app.get("/api/system-health")
    @require_role("admin")
    def system_health():
        readiness, _ = readiness_report()
        failed_executions = RuleExecution.query.filter_by(status="failed").order_by(
            RuleExecution.started_at.desc()).limit(10).all()
        inactive_sources = DataSource.query.filter_by(is_active=False).count()
        disabled_rules = AuditRule.query.filter_by(schedule_enabled=False).count()
        failed_syncs = sum(1 for source in DataSource.query.all() for run in source.sync_runs
                           if run.status == "failed")
        healthy = readiness["status"] == "ready" and not failed_executions and not failed_syncs
        return jsonify(
            overall="healthy" if healthy else "warning",
            readiness=readiness,
            components={
                "database": readiness["checks"].get("database", {}),
                "schema": readiness["checks"].get("schema", {}),
                "rules": {"failed_executions": len(failed_executions),
                          "disabled_schedules": disabled_rules},
                "data_sources": {"inactive": inactive_sources, "failed_syncs": failed_syncs},
            },
            recent_failures=[{
                "execution_id": item.id, "rule_id": item.rule_id,
                "rule_name": item.rule.name, "error": item.error_message,
                "started_at": item.started_at.isoformat()
            } for item in failed_executions],
            recommendations=[
                "Review failed control executions and their bounded evidence.",
                "Verify inactive sources and failed synchronization runs.",
                "Review critical alerts and audit events regularly.",
            ],
        )

    @app.get("/api/data-sources")
    @require_role()
    def list_sources():
        return jsonify([serialize_source(item) for item in DataSource.query.order_by(DataSource.name).all()])

    @app.get("/api/rules")
    @require_role()
    def list_rules():
        return jsonify([serialize_rule(item) for item in AuditRule.query.order_by(AuditRule.id).all()])

    @app.post("/api/rules")
    @require_role("auditor")
    def create_rule():
        payload = request.get_json(silent=True) or {}
        rule_type = str(payload.get("rule_type", "numeric"))
        parameters = dict(payload.get("parameters") or {})
        if rule_type == "numeric":
            parameters.setdefault("operator", payload.get("operator"))
            parameters.setdefault("value", payload.get("threshold_value"))
        required = ("name", "severity", "audit_area_id", "data_source_id")
        if any(payload.get(field) in (None, "") for field in required):
            return jsonify(error="all rule fields are required"), 400
        if rule_type not in RULE_TYPES | {"anomaly"} or payload["severity"] not in SEVERITIES:
            return jsonify(error="invalid rule type or severity"), 400
        area = db.session.get(AuditArea, int(payload["audit_area_id"]))
        source = db.session.get(DataSource, int(payload["data_source_id"]))
        if not area or not source or source.audit_area_id != area.id:
            return jsonify(error="invalid audit area or data source"), 400
        field_name = str(payload.get("field_name", "")).strip()
        try:
            if rule_type == "anomaly":
                detector_name = str(parameters.get("detector", "statistical_zscore"))
                fields = parameters.get("fields") or ([field_name] if field_name else [])
                parameters["detector"] = detector_name
                parameters["fields"] = list(fields)
                get_detector(detector_name).detect(
                    [], fields=fields,
                    sensitivity=parameters.get("sensitivity", 0.5),
                    confidence_threshold=parameters.get("confidence_threshold", 0.8),
                    max_evidence=parameters.get("max_evidence", app.config["EVIDENCE_SAMPLE_LIMIT"]),
                )
            else:
                evaluate_records([], rule_type=rule_type, field=field_name, parameters=parameters)
        except (InvalidRule, DetectorError, TypeError, ValueError) as exc:
            return jsonify(error=str(exc)), 400
        operator_value = str(parameters.get("operator", "=="))
        threshold = float(parameters.get("value", 0)) if rule_type == "numeric" else 0.0
        schedule_interval = payload.get("schedule_interval_minutes")
        if schedule_interval not in (None, ""):
            try:
                schedule_interval = int(schedule_interval)
                if schedule_interval < 1:
                    raise ValueError
            except (TypeError, ValueError):
                return jsonify(error="schedule_interval_minutes must be a positive integer"), 400
        rule = AuditRule(name=str(payload["name"]).strip(), description=str(payload.get("description", "")).strip(),
                         field_name=field_name, operator=operator_value,
                         threshold_value=threshold, rule_type=rule_type, parameters=parameters,
                         schedule_interval_minutes=schedule_interval,
                         next_run_at=utcnow() if schedule_interval else None,
                         severity=payload["severity"], audit_area=area, data_source=source)
        db.session.add(rule)
        db.session.flush()
        record_event("rule_created", "audit_rule", rule.id, {"name": rule.name})
        db.session.commit()
        return jsonify(serialize_rule(rule)), 201

    @app.post("/api/rules/<int:rule_id>/run")
    @require_role("auditor")
    def run_rule(rule_id):
        rule = db.get_or_404(AuditRule, rule_id)
        if not rule.is_active:
            return jsonify(error="rule is inactive"), 409
        execution = execute_rule(rule, trigger="manual")
        alarm = None
        if execution.matched_records:
            alarm = Alarm.query.filter_by(rule_id=rule.id).order_by(Alarm.id.desc()).first()
        record_event("rule_run", "audit_rule", rule.id,
                     {"execution_id": execution.id, "status": execution.status,
                      "scanned_records": execution.scanned_records,
                      "matched_records": execution.matched_records})
        db.session.commit()
        return jsonify(rule_id=rule.id, execution_id=execution.id, status=execution.status,
                       scanned_records=execution.scanned_records, matched_records=execution.matched_records,
                       alarm_id=alarm.id if alarm else None)

    @app.get("/api/rule-executions")
    @require_role("auditor")
    def list_executions():
        executions = RuleExecution.query.order_by(RuleExecution.started_at.desc()).limit(500).all()
        return jsonify([{"id": item.id, "rule_id": item.rule_id, "rule_name": item.rule.name,
                         "status": item.status, "trigger": item.trigger,
                         "scanned_records": item.scanned_records, "matched_records": item.matched_records,
                         "error_message": item.error_message,
                         "started_at": item.started_at.isoformat(),
                         "finished_at": item.finished_at.isoformat() if item.finished_at else None}
                        for item in executions])

    @app.get("/api/rules/<int:rule_id>/schedule")
    @require_role("auditor")
    def get_schedule(rule_id):
        return jsonify(inspect_schedule(db.get_or_404(AuditRule, rule_id)))

    @app.patch("/api/rules/<int:rule_id>/schedule")
    @require_role("auditor")
    def update_schedule(rule_id):
        rule = db.get_or_404(AuditRule, rule_id)
        payload = request.get_json(silent=True) or {}
        try:
            if payload.get("enabled") is False:
                result = disable_schedule(rule)
                action = "schedule_disabled"
            elif payload.get("enabled") is True:
                interval = payload.get("interval_minutes", rule.schedule_interval_minutes)
                if isinstance(interval, str) and interval.isdigit():
                    interval = int(interval)
                result = resume_schedule(rule, interval_minutes=interval,
                                         run_immediately=bool(payload.get("run_immediately", False)))
                action = "schedule_resumed"
            else:
                return jsonify(error="enabled must be true or false"), 400
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
        record_event(action, "audit_rule", rule.id, result)
        db.session.commit()
        return jsonify(result)

    @app.get("/api/alarms")
    @require_role()
    def list_alarms():
        query = Alarm.query
        if request.args.get("status") in STATUSES:
            query = query.filter_by(status=request.args["status"])
        return jsonify([serialize_alarm(item) for item in query.order_by(Alarm.created_at.desc()).all()])

    @app.patch("/api/alarms/<int:alarm_id>/status")
    @require_role("auditor")
    def update_alarm(alarm_id):
        alarm = db.get_or_404(Alarm, alarm_id)
        status = (request.get_json(silent=True) or {}).get("status")
        if status not in STATUSES:
            return jsonify(error="invalid status"), 400
        previous_status = alarm.status
        alarm.status = status
        alarm.updated_at = utcnow()
        add_alarm_activity(alarm, "status", from_value=previous_status, to_value=status)
        record_event("alarm_status_changed", "alarm", alarm.id, {"status": status})
        db.session.commit()
        return jsonify(serialize_alarm(alarm))

    with app.app_context():
        if app.config.get("AUTO_CREATE_SCHEMA", True):
            db.create_all()
        if app.config.get("AUTO_CREATE_SCHEMA", True) and not app.config.get("TESTING"):
            seed_demo_data()
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")),
            debug=os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"})
