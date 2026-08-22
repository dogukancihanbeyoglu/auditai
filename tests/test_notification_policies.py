import pytest

from app import create_app
from models import (Alarm, AuditArea, AuditEvent, AuditRule, DataSource, Notification,
                    NotificationPolicy, User, db)
from security import hash_password


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "SECRET_KEY": "policy-test-secret",
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'policies.db'}"})
    with application.app_context():
        area = AuditArea(name="Payments")
        source = DataSource(name="Ledger", audit_area=area, config={"records": [{"id": 1, "amount": 500}]})
        rule = AuditRule(name="Large payment", field_name="amount", operator=">", threshold_value=100,
                         severity="high", audit_area=area, data_source=source)
        db.session.add_all([
            area, source, rule,
            User(email="admin@test.invalid", password_hash=hash_password("admin-password-123"), role="admin"),
            User(email="auditor@test.invalid", password_hash=hash_password("auditor-password-123"), role="auditor"),
            User(email="viewer@test.invalid", password_hash=hash_password("viewer-password-123"), role="viewer"),
            User(email="disabled@test.invalid", password_hash=hash_password("disabled-password-123"),
                 role="auditor", is_active=False),
        ])
        db.session.commit()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, role):
    return client.post("/api/auth/login", json={"email": f"{role}@test.invalid",
                                                "password": f"{role}-password-123"})


def test_assignee_options_are_role_protected_and_safely_filtered(client):
    assert client.get("/api/alerts/assignee-options").status_code == 401
    login(client, "viewer")
    assert client.get("/api/alerts/assignee-options").status_code == 403
    client.post("/api/auth/logout")
    login(client, "auditor")
    options = client.get("/api/alerts/assignee-options").get_json()
    assert [(item["email"], item["role"]) for item in options] == [
        ("admin@test.invalid", "admin"), ("auditor@test.invalid", "auditor")]
    assert all(set(item) == {"id", "email", "role"} for item in options)


def test_policy_crud_is_admin_only_and_auditable(client, app):
    login(client, "auditor")
    assert client.get("/api/notification-policies").status_code == 200
    assert client.post("/api/notification-policies", json={"severity": "high", "channel": "email",
                                                            "recipient": "audit@test.invalid"}).status_code == 403
    client.post("/api/auth/logout")
    login(client, "admin")
    created = client.post("/api/notification-policies", json={"severity": "high", "channel": "email",
                                                               "recipient": "audit@test.invalid"})
    assert created.status_code == 201
    policy_id = created.get_json()["id"]
    assert client.patch(f"/api/notification-policies/{policy_id}", json={"enabled": False}).get_json()["enabled"] is False
    assert len(client.get("/api/notification-policies").get_json()) == 1
    assert client.delete(f"/api/notification-policies/{policy_id}").status_code == 204
    with app.app_context():
        assert AuditEvent.query.filter_by(action="notification_policy_created").count() == 1
        assert AuditEvent.query.filter_by(action="notification_policy_updated").count() == 1
        assert AuditEvent.query.filter_by(action="notification_policy_deleted").count() == 1


@pytest.mark.parametrize("payload,error", [
    ({"severity": "urgent", "channel": "email", "recipient": "a@test.invalid"}, "severity"),
    ({"severity": "high", "channel": "sms", "recipient": "123"}, "channel"),
    ({"severity": "high", "channel": "email", "recipient": "not-email"}, "email recipient"),
    ({"severity": "high", "channel": "webhook", "recipient": "https://secret.invalid/hook"}, "configured-webhook"),
])
def test_policy_validation_never_accepts_adapter_secrets(client, payload, error):
    login(client, "admin")
    response = client.post("/api/notification-policies", json=payload)
    assert response.status_code == 400
    assert error in response.get_json()["error"]


def test_policy_test_action_only_queues_delivery(client, app):
    login(client, "admin")
    policy = client.post("/api/notification-policies", json={"severity": "any", "channel": "webhook",
                                                              "recipient": "configured-webhook"}).get_json()
    response = client.post(f"/api/notification-policies/{policy['id']}/test")
    assert response.status_code == 201
    assert response.get_json()["status"] == "pending"
    with app.app_context():
        notification = Notification.query.one()
        assert notification.metadata_json["test"] is True
        assert notification.metadata_json["notification_policy_id"] == policy["id"]
        assert AuditEvent.query.filter_by(action="notification_policy_test_queued").count() == 1


def test_alarm_creation_triggers_matching_enabled_policies(client, app):
    login(client, "admin")
    high = client.post("/api/notification-policies", json={"severity": "high", "channel": "email",
                                                            "recipient": "audit@test.invalid"}).get_json()
    client.post("/api/notification-policies", json={"severity": "critical", "channel": "in_app",
                                                     "recipient": "auditors"})
    client.post("/api/notification-policies", json={"severity": "any", "channel": "webhook",
                                                     "recipient": "configured-webhook", "enabled": False})
    result = client.post("/api/rules/1/run")
    assert result.status_code == 200
    with app.app_context():
        assert Alarm.query.count() == 1
        notifications = Notification.query.all()
        assert len(notifications) == 1
        assert notifications[0].channel == "email"
        assert notifications[0].recipient == "audit@test.invalid"
        assert notifications[0].status == "pending"
        assert notifications[0].metadata_json["notification_policy_id"] == high["id"]


def test_no_policies_preserves_default_in_app_notification(client, app):
    login(client, "admin")
    assert client.post("/api/rules/1/run").status_code == 200
    with app.app_context():
        notification = Notification.query.one()
        assert notification.channel == "in_app"
        assert notification.status == "delivered"
        assert NotificationPolicy.query.count() == 0
