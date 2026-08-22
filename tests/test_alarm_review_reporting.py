import csv
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone

import pytest

from app import create_app
from models import (Alarm, AlarmActivity, AuditArea, AuditEvent, AuditRule, DataSource,
                    RiskScore, RuleExecution, User, db)
from security import hash_password


NOW = datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "SECRET_KEY": "review-test-secret",
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'review.db'}"})
    with application.app_context():
        area = AuditArea(name="Payments")
        other_area = AuditArea(name="Other")
        source = DataSource(name="Ledger", audit_area=area, config={"records": []})
        other_source = DataSource(name="Other ledger", audit_area=other_area, config={"records": []})
        rule = AuditRule(name="=Risky formula", field_name="amount", operator=">", threshold_value=10,
                         severity="high", audit_area=area, data_source=source)
        other_rule = AuditRule(name="Other rule", field_name="amount", operator=">", threshold_value=10,
                               severity="low", audit_area=other_area, data_source=other_source)
        db.session.add_all([area, other_area, source, other_source, rule, other_rule])
        db.session.flush()
        db.session.add_all([
            Alarm(title="+Review this", message="Evidence", severity="high", status="open",
                  affected_records=[{"invoice": "=cmd"}], rule=rule, audit_area=area, data_source=source,
                  created_at=NOW),
            Alarm(title="Other", message="Other", severity="low", status="resolved", affected_records=[],
                  rule=other_rule, audit_area=other_area, data_source=other_source,
                  created_at=NOW - timedelta(days=10)),
            RuleExecution(rule=rule, status="completed", trigger="manual", scanned_records=10,
                          matched_records=1, started_at=NOW, finished_at=NOW),
            RuleExecution(rule=other_rule, status="completed", trigger="manual", scanned_records=50,
                          matched_records=0, started_at=NOW - timedelta(days=10), finished_at=NOW),
            RiskScore(rule=rule, audit_area=area, score=75, level="critical", alarm_count=1,
                      open_alarm_count=1, components={}, explanation="test", calculated_at=NOW),
            RiskScore(rule=other_rule, audit_area=other_area, score=10, level="low", alarm_count=1,
                      open_alarm_count=0, components={}, explanation="test", calculated_at=NOW - timedelta(days=10)),
            User(email="auditor@test.invalid", password_hash=hash_password("auditor-password-123"), role="auditor"),
            User(email="assignee@test.invalid", password_hash=hash_password("assignee-password-123"), role="auditor"),
            User(email="viewer@test.invalid", password_hash=hash_password("viewer-password-123"), role="viewer"),
        ])
        db.session.commit()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, role):
    return client.post("/api/auth/login", json={"email": f"{role}@test.invalid",
                                                "password": f"{role}-password-123"})


def test_assignment_notes_and_status_form_persistent_timeline(client, app):
    assert login(client, "auditor").status_code == 200
    with app.app_context():
        assignee_id = User.query.filter_by(email="assignee@test.invalid").one().id
    assigned = client.post("/api/alerts/1/assignment", json={"user_id": assignee_id})
    assert assigned.status_code == 200
    assert assigned.get_json()["assignee"]["email"] == "assignee@test.invalid"
    note = client.post("/api/alerts/1/notes", json={"note": "Invoice owner contacted."})
    assert note.status_code == 201
    assert client.patch("/api/alarms/1/status", json={"status": "acknowledged"}).status_code == 200
    review = client.get("/api/alerts/1/review").get_json()
    assert [item["event_type"] for item in review["timeline"]] == ["assignment", "note", "status"]
    assert review["timeline"][-1]["from_value"] == "open"
    assert review["timeline"][-1]["to_value"] == "acknowledged"
    with app.app_context():
        assert AlarmActivity.query.count() == 3
        assert AuditEvent.query.filter_by(action="alarm_note_added").count() == 1


def test_assignment_validation_and_role_protection(client, app):
    login(client, "viewer")
    assert client.get("/api/alerts/1/review").status_code == 403
    client.post("/api/auth/logout")
    login(client, "auditor")
    with app.app_context():
        viewer_id = User.query.filter_by(role="viewer").one().id
    assert client.post("/api/alerts/1/assignment", json={"user_id": viewer_id}).status_code == 400
    assert client.post("/api/alerts/1/notes", json={"note": " "}).status_code == 400
    assert client.post("/api/alerts/1/notes", json={"note": "x" * 4001}).status_code == 400


def test_management_report_filters_area_date_and_risk(client):
    login(client, "viewer")
    query = "/api/reports/management-summary?audit_area_id=1&from=2026-01-31T00:00:00%2B00:00"
    summary = client.get(query).get_json()
    assert summary["execution_count"] == 1
    assert summary["scanned_records"] == 10
    assert summary["alarm_count"] == 1
    assert summary["risk_snapshot_count"] == 1
    assert summary["risk_by_level"] == {"critical": 1}
    assert summary["average_risk_score"] == 75


def test_evidence_package_is_bounded_safe_and_audited(client, app):
    login(client, "auditor")
    response = client.get("/api/reports/evidence-package.zip?audit_area_id=1")
    assert response.status_code == 200
    assert response.mimetype == "application/zip"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        assert sorted(archive.namelist()) == ["alarms.csv", "evidence/alarm-1.json", "manifest.json"]
        rows = list(csv.reader(io.StringIO(archive.read("alarms.csv").decode())))
        assert rows[1][1].startswith("'+")
        assert rows[1][4].startswith("'=")
        evidence = json.loads(archive.read("evidence/alarm-1.json"))
        assert evidence["affected_records"] == [{"invoice": "=cmd"}]
        assert json.loads(archive.read("manifest.json"))["alarm_count"] == 1
    with app.app_context():
        event = AuditEvent.query.filter_by(action="evidence_package_exported").one()
        assert event.details["alarm_count"] == 1
