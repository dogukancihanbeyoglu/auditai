import pytest

from app import create_app
from models import Alarm, AuditArea, AuditEvent, AuditRule, DataSource, RiskScore, User, db
from security import hash_password


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "SECRET_KEY": "risk-tests",
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'risk.db'}"})
    with application.app_context():
        area = AuditArea(name="Payments")
        source = DataSource(name="Ledger", audit_area=area, config={"records": []})
        rule = AuditRule(name="Payment control", field_name="amount", operator=">", threshold_value=100,
                         severity="critical", trigger_count=4, consecutive_failures=2,
                         audit_area=area, data_source=source)
        db.session.add_all([area, source, rule,
            User(email="auditor@example.test", password_hash=hash_password("auditor-password-123"), role="auditor"),
            User(email="viewer@example.test", password_hash=hash_password("viewer-password-123"), role="viewer")])
        db.session.flush()
        db.session.add_all([
            Alarm(title="Critical open", message="Evidence", severity="critical", status="open",
                  affected_records=[{"id": item} for item in range(120)], rule=rule, audit_area=area, data_source=source),
            Alarm(title="High acknowledged", message="Evidence", severity="high", status="acknowledged",
                  affected_records=[], rule=rule, audit_area=area, data_source=source),
            Alarm(title="Low open", message="Evidence", severity="low", status="open",
                  affected_records=[], rule=rule, audit_area=area, data_source=source),
        ])
        db.session.commit()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, role="auditor"):
    return client.post("/api/auth/login", json={"email": f"{role}@example.test", "password": f"{role}-password-123"})


def test_risk_endpoints_require_auditor(client):
    assert client.get("/api/risk-scores").status_code == 401
    login(client, "viewer")
    assert client.get("/api/risk-scores").status_code == 403
    assert client.post("/api/alerts/bulk-status", json={"alarm_ids": [1], "action": "resolve"}).status_code == 403


def test_calculation_is_deterministic_explainable_and_persistent(client, app):
    login(client)
    first = client.post("/api/risk-scores/calculate", json={})
    assert first.status_code == 201
    score = first.get_json()[0]
    assert score["score"] == 100.0
    assert score["level"] == "critical"
    assert score["components"] == {"severity_status_points": 117.5, "trigger_points": 5.0,
                                   "failure_points": 10, "raw_score": 132.5, "capped_at": 100}
    assert "capped at 100" in score["explanation"]
    second = client.post("/api/risk-scores/calculate", json={}).get_json()[0]
    assert second["score"] == score["score"]
    listed = client.get("/api/risk-scores?limit=1").get_json()
    assert len(listed) == 1
    with app.app_context():
        assert RiskScore.query.count() == 2
        assert AuditEvent.query.filter_by(action="risk_scores_calculated").count() == 2


def test_alarm_detail_bounds_evidence(client):
    login(client)
    detail = client.get("/api/alerts/1")
    assert detail.status_code == 200
    payload = detail.get_json()
    assert payload["affected_record_count"] == 120
    assert len(payload["affected_records"]) == 100
    assert payload["affected_records_truncated"] is True
    assert payload["rule"]["name"] == "Payment control"


def test_bulk_status_is_atomic_audited_and_validates_transitions(client, app):
    login(client)
    missing = client.post("/api/alerts/bulk-status", json={"alarm_ids": [1, 999], "action": "resolve"})
    assert missing.status_code == 404
    with app.app_context():
        assert db.session.get(Alarm, 1).status == "open"

    acknowledged = client.post("/api/alerts/bulk-status", json={"alarm_ids": [1, 3], "action": "acknowledge"})
    assert acknowledged.status_code == 200
    assert acknowledged.get_json()["updated"] == 2
    invalid = client.post("/api/alerts/bulk-status", json={"alarm_ids": [1], "action": "acknowledge"})
    assert invalid.status_code == 409
    resolved = client.post("/api/alerts/bulk-status", json={"alarm_ids": [1, 2], "action": "resolve"})
    assert resolved.status_code == 200
    with app.app_context():
        assert [db.session.get(Alarm, item).status for item in (1, 2)] == ["resolved", "resolved"]
        assert AuditEvent.query.filter_by(action="alarms_bulk_status_changed").count() == 2


@pytest.mark.parametrize("payload,status", [
    ({"alarm_ids": [], "action": "resolve"}, 400),
    ({"alarm_ids": [True], "action": "resolve"}, 400),
    ({"alarm_ids": [1, 1], "action": "resolve"}, 400),
    ({"alarm_ids": list(range(1, 102)), "action": "resolve"}, 413),
    ({"alarm_ids": [1], "action": "delete"}, 400),
])
def test_bulk_input_limits(client, payload, status):
    login(client)
    assert client.post("/api/alerts/bulk-status", json=payload).status_code == status
