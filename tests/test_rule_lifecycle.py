import pytest

from app import create_app
from models import AuditArea, AuditEvent, AuditRule, DataSource, db


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "AUTH_REQUIRED": False,
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'lifecycle.db'}"})
    with application.app_context():
        area = AuditArea(name="Payments")
        source = DataSource(name="Ledger", audit_area=area,
                            config={"records": [{"id": 1, "amount": 250}]})
        rule = AuditRule(name="Large payment", description="Original", field_name="amount", operator=">",
                         threshold_value=100, parameters={"operator": ">", "value": 100}, severity="high",
                         schedule_interval_minutes=60, next_run_at=None, audit_area=area, data_source=source)
        db.session.add_all([area, source, rule])
        db.session.commit()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def test_rule_detail_exposes_schedule_and_execution_views(client):
    initial = client.get("/api/rules/1").get_json()
    assert initial["schedule"]["last_execution"] is None
    client.post("/api/rules/1/run")
    detail = client.get("/api/rules/1").get_json()
    assert detail["last_run_at"] is not None
    assert detail["schedule"]["last_execution"]["status"] == "completed"
    assert detail["schedule"]["last_execution"]["trigger"] == "manual"
    schedule = client.get("/api/rules/1/schedule").get_json()
    assert schedule["last_execution"]["id"] == detail["schedule"]["last_execution"]["id"]
    assert "next_run_at" in schedule
    listed = client.get("/api/rules").get_json()[0]
    assert listed["schedule"]["last_execution"]["id"] == schedule["last_execution"]["id"]


def test_scheduler_aggregate_status(client):
    status = client.get("/api/scheduler/status")
    assert status.status_code == 200
    assert status.get_json()["configured_rules"] == 1
    assert status.get_json()["enabled_rules"] == 1
    client.post("/api/rules/1/run")
    assert client.get("/api/scheduler/status").get_json()["last_scheduled_execution"] is None


def test_update_metadata_and_unexecuted_definition(client, app):
    changed = client.patch("/api/rules/1", json={"name": "Material payment", "severity": "critical"})
    assert changed.status_code == 200
    assert changed.get_json()["name"] == "Material payment"
    definition = client.patch("/api/rules/1", json={
        "rule_type": "numeric", "field_name": "amount",
        "parameters": {"operator": ">=", "value": 200},
    })
    assert definition.status_code == 200
    assert definition.get_json()["threshold_value"] == 200
    with app.app_context():
        assert AuditEvent.query.filter_by(action="rule_updated").count() == 2


def test_executed_definition_is_immutable_but_metadata_can_change(client):
    client.post("/api/rules/1/run")
    rejected = client.patch("/api/rules/1", json={"parameters": {"operator": ">", "value": 500}})
    assert rejected.status_code == 409
    assert "new rule version" in rejected.get_json()["error"]
    assert client.patch("/api/rules/1", json={"description": "Updated context"}).status_code == 200


def test_disable_stops_schedule_and_enable_does_not_silently_resume(client):
    disabled = client.patch("/api/rules/1/active", json={"is_active": False})
    assert disabled.status_code == 200
    payload = disabled.get_json()
    assert payload["is_active"] is False
    assert payload["schedule"]["enabled"] is False
    enabled = client.patch("/api/rules/1/active", json={"is_active": True}).get_json()
    assert enabled["is_active"] is True
    assert enabled["schedule"]["enabled"] is False
    resumed = client.patch("/api/rules/1/schedule", json={"enabled": True, "interval_minutes": 30})
    assert resumed.status_code == 200
    assert resumed.get_json()["enabled"] is True


def test_delete_unused_rule_but_preserve_audit_evidence(client, app):
    response = client.delete("/api/rules/1")
    assert response.status_code == 204
    with app.app_context():
        assert db.session.get(AuditRule, 1) is None
        assert AuditEvent.query.filter_by(action="rule_deleted").count() == 1


def test_delete_executed_rule_is_rejected(client):
    client.post("/api/rules/1/run")
    response = client.delete("/api/rules/1")
    assert response.status_code == 409
    assert response.get_json()["dependencies"]["executions"] == 1


@pytest.mark.parametrize("path,payload", [
    ("/api/rules/1", {}),
    ("/api/rules/1", {"unknown": True}),
    ("/api/rules/1", {"name": ""}),
    ("/api/rules/1/active", {"is_active": "false"}),
])
def test_lifecycle_input_validation(client, path, payload):
    assert client.patch(path, json=payload).status_code == 400
