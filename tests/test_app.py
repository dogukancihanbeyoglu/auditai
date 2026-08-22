import pytest

from app import create_app
from models import AuditArea, AuditRule, DataSource, db


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "AUTH_REQUIRED": False,
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    with application.app_context():
        area = AuditArea(name="Payments", description="Payment controls")
        source = DataSource(name="Test ledger", audit_area=area,
                            config={"records": [{"id": 1, "amount": 50}, {"id": 2, "amount": 250}]})
        db.session.add_all([area, source])
        db.session.commit()
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


def test_health_and_dashboard(client):
    assert client.get("/health").get_json()["status"] == "ok"
    page = client.get("/")
    assert page.status_code == 200
    assert b"Continuous control monitoring overview" in page.data
    assert b"Data Sources" in page.data


def test_dashboard_insights_and_source_overview_contract(client):
    insights = client.get("/api/dashboard/insights")
    assert insights.status_code == 200
    payload = insights.get_json()
    assert len(payload["daily_alarms"]) == 7
    assert payload["source_types"] == {"synthetic": 1}
    assert payload["top_areas"][0]["name"] == "Payments"
    source = client.get("/api/data-sources").get_json()[0]
    assert source["audit_area_name"] == "Payments"
    assert source["mapping_count"] == 0
    assert source["quality_check_count"] == 0


def test_workspace_pages_are_available(client):
    for path, heading in {
        "/data-sources": b"Upload and inspect controlled datasets",
        "/audit-areas": b"Structure and manage the audit universe",
        "/data-governance": b"Map fields and execute persistent data-quality controls",
        "/rules": b"Configure and run audit controls",
        "/executions": b"Review immutable control run history",
        "/alerts": b"Triage exceptions, inspect evidence and run bulk actions",
        "/risk-scores": b"Calculate transparent risk from persisted control evidence",
        "/reports": b"Management-level control analytics",
        "/notifications": b"Monitor delivery outbox status",
        "/audit-logs": b"Review security and business events",
        "/settings": b"Manage the local workspace",
    }.items():
        response = client.get(path)
        assert response.status_code == 200
        assert heading in response.data


def test_create_run_and_resolve_rule(client):
    area = client.get("/api/audit-areas").get_json()[0]
    source = client.get("/api/data-sources").get_json()[0]
    response = client.post("/api/rules", json={"name": "Large payment", "field_name": "amount",
        "operator": ">", "threshold_value": 100, "severity": "high",
        "audit_area_id": area["id"], "data_source_id": source["id"]})
    assert response.status_code == 201
    rule = response.get_json()

    result = client.post(f"/api/rules/{rule['id']}/run").get_json()
    assert result["scanned_records"] == 2
    assert result["matched_records"] == 1
    assert result["alarm_id"] is not None

    alarms = client.get("/api/alarms").get_json()
    assert alarms[0]["affected_records"][0]["id"] == 2
    updated = client.patch(f"/api/alarms/{alarms[0]['id']}/status", json={"status": "resolved"})
    assert updated.status_code == 200
    assert updated.get_json()["status"] == "resolved"


def test_rule_validation(client):
    response = client.post("/api/rules", json={"name": "Incomplete"})
    assert response.status_code == 400
    assert "required" in response.get_json()["error"]


def test_advanced_rule_api_records_execution_history(client):
    area = client.get("/api/audit-areas").get_json()[0]
    source = client.get("/api/data-sources").get_json()[0]
    response = client.post("/api/rules", json={
        "name": "Amount is present", "field_name": "amount", "rule_type": "null",
        "parameters": {"operator": "not_null"}, "severity": "medium",
        "audit_area_id": area["id"], "data_source_id": source["id"],
        "schedule_interval_minutes": 60,
    })
    assert response.status_code == 201
    rule = response.get_json()
    assert rule["rule_type"] == "null"
    assert rule["schedule_interval_minutes"] == 60

    result = client.post(f"/api/rules/{rule['id']}/run").get_json()
    assert result["status"] == "completed"
    assert result["matched_records"] == 2
    history = client.get("/api/rule-executions").get_json()
    assert history[0]["id"] == result["execution_id"]
    assert history[0]["rule_name"] == "Amount is present"

    disabled = client.patch(f"/api/rules/{rule['id']}/schedule", json={"enabled": False})
    assert disabled.status_code == 200
    assert disabled.get_json()["enabled"] is False
    resumed = client.patch(f"/api/rules/{rule['id']}/schedule",
                           json={"enabled": True, "interval_minutes": 30})
    assert resumed.status_code == 200
    assert resumed.get_json()["interval_minutes"] == 30
