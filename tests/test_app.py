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
    assert b"Run control" in page.data


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
