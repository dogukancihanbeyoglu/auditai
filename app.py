"""AuditAI: a functional audit-rule and alert-management prototype."""

import operator
import os
import secrets
from datetime import timedelta
from pathlib import Path

import click
from flask import Flask, jsonify, render_template, request

from models import Alarm, AuditArea, AuditRule, DataSource, User, db, utcnow
from notifications import notification_service
from reporting import reporting_bp
from security import hash_password, record_event, require_role, security_bp


OPERATORS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq}
SEVERITIES = {"low", "medium", "high", "critical"}
STATUSES = {"open", "acknowledged", "resolved"}


def serialize_area(area):
    return {"id": area.id, "name": area.name, "description": area.description, "is_active": area.is_active}


def serialize_source(source):
    records = source.config.get("records", []) if source.config else []
    return {"id": source.id, "name": source.name, "source_type": source.source_type,
            "audit_area_id": source.audit_area_id, "record_count": len(records)}


def serialize_rule(rule):
    return {"id": rule.id, "name": rule.name, "description": rule.description,
            "field_name": rule.field_name, "operator": rule.operator,
            "threshold_value": rule.threshold_value, "severity": rule.severity,
            "is_active": rule.is_active, "trigger_count": rule.trigger_count,
            "audit_area_id": rule.audit_area_id, "data_source_id": rule.data_source_id,
            "last_run_at": rule.last_run_at.isoformat() if rule.last_run_at else None}


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
    app.config.update(SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", f"sqlite:///{default_db}"),
                      SQLALCHEMY_TRACK_MODIFICATIONS=False, JSON_SORT_KEYS=False,
                      SECRET_KEY=os.environ.get("SESSION_SECRET") or secrets.token_hex(32),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                      SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "").lower() in {"1", "true", "yes"},
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=8), AUTH_REQUIRED=True)
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    app.register_blueprint(security_bp)
    app.register_blueprint(reporting_bp)

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
    from data_sources import data_sources_bp
    app.register_blueprint(data_sources_bp)

    @app.get("/")
    @require_role()
    def index():
        return render_template("admin_demo.html")

    @app.get("/health")
    def health():
        return jsonify(status="ok", service="auditai", database="connected")

    @app.get("/api/summary")
    @require_role()
    def summary():
        return jsonify(audit_areas=AuditArea.query.count(), data_sources=DataSource.query.count(),
                       active_rules=AuditRule.query.filter_by(is_active=True).count(),
                       open_alarms=Alarm.query.filter_by(status="open").count())

    @app.get("/api/audit-areas")
    @require_role()
    def list_areas():
        return jsonify([serialize_area(item) for item in AuditArea.query.order_by(AuditArea.name).all()])

    @app.post("/api/audit-areas")
    @require_role("auditor")
    def create_area():
        payload = request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        if not name:
            return jsonify(error="name is required"), 400
        if AuditArea.query.filter_by(name=name).first():
            return jsonify(error="audit area already exists"), 409
        area = AuditArea(name=name, description=str(payload.get("description", "")).strip())
        db.session.add(area)
        db.session.flush()
        record_event("audit_area_created", "audit_area", area.id, {"name": area.name})
        db.session.commit()
        return jsonify(serialize_area(area)), 201

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
        required = ("name", "field_name", "operator", "threshold_value", "severity", "audit_area_id", "data_source_id")
        if any(payload.get(field) in (None, "") for field in required):
            return jsonify(error="all rule fields are required"), 400
        if payload["operator"] not in OPERATORS or payload["severity"] not in SEVERITIES:
            return jsonify(error="invalid operator or severity"), 400
        area = db.session.get(AuditArea, int(payload["audit_area_id"]))
        source = db.session.get(DataSource, int(payload["data_source_id"]))
        if not area or not source or source.audit_area_id != area.id:
            return jsonify(error="invalid audit area or data source"), 400
        try:
            threshold = float(payload["threshold_value"])
        except (TypeError, ValueError):
            return jsonify(error="threshold_value must be numeric"), 400
        rule = AuditRule(name=str(payload["name"]).strip(), description=str(payload.get("description", "")).strip(),
                         field_name=str(payload["field_name"]).strip(), operator=payload["operator"],
                         threshold_value=threshold, severity=payload["severity"], audit_area=area, data_source=source)
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
        compare = OPERATORS[rule.operator]
        records = (rule.data_source.config or {}).get("records", [])
        matches = []
        for record in records:
            value = record.get(rule.field_name)
            try:
                if value is not None and compare(float(value), rule.threshold_value):
                    matches.append(record)
            except (TypeError, ValueError):
                continue
        rule.last_run_at = utcnow()
        if matches:
            alarm = Alarm(title=rule.name, message=f"{len(matches)} record(s) matched: {rule.field_name} {rule.operator} {rule.threshold_value:g}",
                          severity=rule.severity, affected_records=matches, rule=rule,
                          audit_area=rule.audit_area, data_source=rule.data_source)
            rule.trigger_count += 1
            db.session.add(alarm)
            db.session.flush()
            notification_service.notify(f"Audit alert: {rule.name}", alarm.message,
                                        metadata={"alarm_id": alarm.id, "severity": alarm.severity})
        record_event("rule_run", "audit_rule", rule.id,
                     {"scanned_records": len(records), "matched_records": len(matches)})
        db.session.commit()
        return jsonify(rule_id=rule.id, scanned_records=len(records), matched_records=len(matches),
                       alarm_id=alarm.id if matches else None)

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
        alarm.status = status
        alarm.updated_at = utcnow()
        record_event("alarm_status_changed", "alarm", alarm.id, {"status": status})
        db.session.commit()
        return jsonify(serialize_alarm(alarm))

    with app.app_context():
        db.create_all()
        if not app.config.get("TESTING"):
            seed_demo_data()
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")),
            debug=os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"})
