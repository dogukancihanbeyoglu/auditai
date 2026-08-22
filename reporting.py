"""Read-only reporting and notification API endpoints."""

import csv
import io

from flask import Blueprint, Response, jsonify

from models import Alarm, Notification
from security import require_role


reporting_bp = Blueprint("reporting", __name__)


@reporting_bp.get("/api/reports/alarms.csv")
@require_role("auditor")
def alarms_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "title", "severity", "status", "rule", "audit_area", "created_at"])
    for alarm in Alarm.query.order_by(Alarm.created_at.desc()).all():
        writer.writerow([alarm.id, alarm.title, alarm.severity, alarm.status,
                         alarm.rule.name, alarm.audit_area.name, alarm.created_at.isoformat()])
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=auditai-alarms.csv"})


@reporting_bp.get("/api/notifications")
@require_role("auditor")
def notifications():
    items = Notification.query.order_by(Notification.created_at.desc()).limit(100).all()
    return jsonify([{"id": item.id, "channel": item.channel, "recipient": item.recipient,
                     "subject": item.subject, "body": item.body, "status": item.status,
                     "metadata": item.metadata_json, "created_at": item.created_at.isoformat()}
                    for item in items])
