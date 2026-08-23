from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app import create_app
from models import Alarm, AuditArea, AuditEvent, AuditRule, DataSource, Notification, RuleExecution, db
from notifications import NotificationService


NOW = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "AUTH_REQUIRED": False,
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'reports.db'}"})
    with application.app_context():
        area = AuditArea(name="Payments")
        source = DataSource(name="Ledger", audit_area=area, config={"records": []})
        rule = AuditRule(name="High payment", field_name="amount", operator=">", threshold_value=100,
                         severity="high", audit_area=area, data_source=source)
        db.session.add_all([area, source, rule])
        db.session.flush()
        db.session.add_all([
            RuleExecution(rule=rule, status="completed", trigger="manual", scanned_records=100,
                          matched_records=5, started_at=NOW - timedelta(days=2), finished_at=NOW - timedelta(days=2)),
            RuleExecution(rule=rule, status="failed", trigger="scheduled", scanned_records=0,
                          matched_records=0, started_at=NOW, finished_at=NOW),
            Alarm(title="High payment", message="5 matches", severity="high", status="open",
                  affected_records=[], rule=rule, audit_area=area, data_source=source,
                  created_at=NOW - timedelta(days=2)),
            Alarm(title="Resolved item", message="resolved", severity="low", status="resolved",
                  affected_records=[], rule=rule, audit_area=area, data_source=source, created_at=NOW),
        ])
        db.session.commit()
    return application


def test_filterable_histories_and_management_summary(app):
    client = app.test_client()
    executions = client.get("/api/reports/executions?status=failed&trigger=scheduled").get_json()
    assert len(executions) == 1
    assert executions[0]["status"] == "failed"
    alarms = client.get("/api/reports/alarms?severity=high&status=open").get_json()
    assert len(alarms) == 1
    summary = client.get("/api/reports/management-summary").get_json()
    assert summary["execution_count"] == 2
    assert summary["scanned_records"] == 100
    assert summary["matched_records"] == 5
    assert summary["match_rate"] == 0.05
    assert summary["alarms_by_severity"] == {"high": 1, "low": 1}
    assert b"High payment" in client.get("/api/reports/alarms.csv?status=open").data
    assert b"Resolved item" not in client.get("/api/reports/alarms.csv?status=open").data


def test_executive_dashboard_and_csv_export(app):
    client = app.test_client()
    response = client.get("/api/reports/executive-dashboard?days=365")
    assert response.status_code == 200
    report = response.get_json()
    assert report["kpis"]["active_rules"] == 1
    assert report["kpis"]["execution_count"] == 2
    assert report["kpis"]["scanned_records"] == 100
    assert report["kpis"]["matched_records"] == 5
    assert report["kpis"]["open_findings"] == 1
    assert report["findings_by_source"] == [{"name": "Ledger", "count": 2}]
    rule = report["rules"][0]
    assert rule["sources"] == ["Ledger"]
    assert rule["execution_count"] == 2
    assert rule["finding_count"] == 2
    assert rule["open_findings"] == 1
    assert rule["priority"] == "high"

    exported = client.get("/api/reports/executive-dashboard.csv?days=365")
    assert exported.status_code == 200
    assert exported.headers["Content-Disposition"].endswith("auditai-yonetici-raporu.csv")
    assert "High payment" in exported.get_data(as_text=True)
    with app.app_context():
        event = AuditEvent.query.filter_by(action="executive_report_exported").one()
        assert event.details["rule_count"] == 1


def test_webhook_delivery_uses_environment_and_mocked_network(app):
    service = NotificationService({"NOTIFICATION_WEBHOOK_URL": "https://example.invalid/audit",
                                   "NOTIFICATION_WEBHOOK_TOKEN": "test-token"})
    with app.app_context():
        item = service.notify("Alert", "Body", channels=["webhook"])
        db.session.commit()
        response = MagicMock(status=204)
        response.__enter__.return_value = response
        with patch("notifications.urllib.request.urlopen", return_value=response) as urlopen:
            result = service.deliver_due(now=NOW)
        assert result == {"delivered": 1, "retrying": 0, "failed": 0}
        assert db.session.get(Notification, item.id).status == "delivered"
        sent_request = urlopen.call_args.args[0]
        assert sent_request.full_url == "https://example.invalid/audit"
        assert sent_request.headers["Authorization"] == "Bearer test-token"


def test_email_delivery_is_mocked_and_credentials_are_not_persisted(app):
    env = {"SMTP_HOST": "smtp.example.invalid", "SMTP_PORT": "2525", "SMTP_FROM": "audit@example.invalid",
           "SMTP_USERNAME": "user", "SMTP_PASSWORD": "secret", "SMTP_USE_TLS": "true"}
    service = NotificationService(env)
    with app.app_context():
        item = service.notify("Alert", "Body", recipient="auditor@example.invalid", channels=["email"])
        db.session.commit()
        smtp = MagicMock()
        smtp.__enter__.return_value = smtp
        with patch("notifications.smtplib.SMTP", return_value=smtp) as smtp_class:
            service.deliver_due(now=NOW)
        smtp_class.assert_called_once_with("smtp.example.invalid", 2525, timeout=10)
        smtp.starttls.assert_called_once()
        smtp.login.assert_called_once_with("user", "secret")
        stored = db.session.get(Notification, item.id)
        assert stored.status == "delivered"
        assert "secret" not in str(stored.metadata_json)


def test_failed_delivery_retries_with_exponential_backoff(app):
    service = NotificationService({"NOTIFICATION_WEBHOOK_URL": "https://example.invalid/audit"})
    with app.app_context():
        item = service.notify("Alert", "Body", channels=["webhook"])
        db.session.commit()
        with patch("notifications.urllib.request.urlopen", side_effect=OSError("temporary failure")):
            first = service.deliver_due(now=NOW, max_attempts=2, base_delay_seconds=30)
            assert first["retrying"] == 1
            stored = db.session.get(Notification, item.id)
            assert stored.status == "retrying"
            assert stored.metadata_json["next_attempt_at"] == (NOW + timedelta(seconds=30)).isoformat()
            assert service.deliver_due(now=NOW + timedelta(seconds=10), max_attempts=2)["failed"] == 0
            second = service.deliver_due(now=NOW + timedelta(seconds=30), max_attempts=2)
            assert second["failed"] == 1
            assert db.session.get(Notification, item.id).status == "failed"
