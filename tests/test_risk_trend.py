from datetime import datetime, timedelta, timezone

import pytest

from app import create_app
from models import Alarm, AuditArea, AuditRule, DataSource, RiskScore, User, db
from security import hash_password


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "SECRET_KEY": "trend-tests",
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'trend.db'}"})
    with application.app_context():
        area = AuditArea(name="Payments")
        source = DataSource(name="Ledger", audit_area=area, config={"records": []})
        rule = AuditRule(name="Payment control", field_name="amount", operator=">", threshold_value=100,
                         severity="high", audit_area=area, data_source=source)
        user = User(email="auditor@example.test", password_hash=hash_password("auditor-password-123"), role="auditor")
        db.session.add_all([area, source, rule, user])
        db.session.flush()
        db.session.add(Alarm(title="Alert", message="Evidence", severity="high", status="open",
                             affected_records=[], rule=rule, audit_area=area, data_source=source))
        for when, score, severity_points, trigger_points in [
            (datetime(2025, 1, 1, tzinfo=timezone.utc), 20, 15, 5),
            (datetime(2025, 2, 1, tzinfo=timezone.utc), 35, 25, 10),
            (datetime(2025, 3, 1, tzinfo=timezone.utc), 30, 25, 5),
        ]:
            db.session.add(RiskScore(
                rule=rule, audit_area=area, score=score, level="medium",
                alarm_count=1, open_alarm_count=1,
                components={"severity_status_points": severity_points, "trigger_points": trigger_points,
                            "failure_points": 0, "raw_score": score, "capped_at": 100},
                explanation="test snapshot", calculated_at=when,
            ))
        db.session.commit()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client):
    return client.post("/api/auth/login", json={"email": "auditor@example.test",
                                                "password": "auditor-password-123"})


def test_trend_requires_authorization(client):
    assert client.get("/api/risk-scores/trend").status_code == 401


def test_period_trend_uses_prior_snapshot_and_explains_component_change(client):
    login(client)
    response = client.get("/api/risk-scores/trend?rule_id=1&from=2025-02-01&to=2025-03-31")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["count"] == 2
    february, march = payload["items"]
    assert february["previous"]["score"] == 20
    assert february["score_change"] == 15
    assert february["score_change_percent"] == 75
    assert february["direction"] == "increased"
    assert february["component_comparison"]["severity_status_points"] == {
        "current": 25, "previous": 15, "change": 10}
    assert march["previous"]["id"] == february["id"]
    assert march["score_change"] == -5
    assert march["direction"] == "decreased"
    assert march["drill_down"] == {
        "rule_id": 1, "audit_area_id": 1, "data_source_id": 1,
        "alarm_ids": [1], "alarm_count": 1, "alarm_ids_truncated": False,
    }


def test_trend_query_is_bounded_and_returns_latest_points(client, app):
    with app.app_context():
        rule = db.session.get(AuditRule, 1)
        area = db.session.get(AuditArea, 1)
        for offset in range(10):
            db.session.add(RiskScore(rule=rule, audit_area=area, score=40 + offset, level="medium",
                                     components={"raw_score": 40 + offset}, explanation="bounded",
                                     calculated_at=datetime(2025, 4, 1, tzinfo=timezone.utc) + timedelta(days=offset)))
        db.session.commit()
    login(client)
    payload = client.get("/api/risk-scores/trend?rule_id=1&limit=2").get_json()
    assert payload["count"] == 2
    assert payload["truncated"] is True
    assert [item["score"] for item in payload["items"]] == [48, 49]
    assert payload["items"][0]["previous"]["score"] == 47


@pytest.mark.parametrize("query", [
    "from=not-a-date",
    "from=2025-03-01&to=2025-02-01",
    "from=2024-01-01&to=2025-12-31",
    "limit=0",
    "rule_id=true",
])
def test_trend_filter_validation(client, query):
    login(client)
    response = client.get(f"/api/risk-scores/trend?{query}")
    assert response.status_code == 400
