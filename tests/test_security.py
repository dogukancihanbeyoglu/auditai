import pytest

from app import create_app
from models import Alarm, AuditArea, AuditEvent, AuditRule, DataSource, Notification, User, db
from security import hash_password


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "SECRET_KEY": "test-only-secret",
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'security.db'}"})
    with application.app_context():
        area = AuditArea(name="Payments")
        source = DataSource(name="Ledger", audit_area=area, config={"records": [{"id": 1, "amount": 500}]})
        rule = AuditRule(name="Large item", field_name="amount", operator=">", threshold_value=100,
                         severity="high", audit_area=area, data_source=source)
        db.session.add_all([area, source, rule,
                            User(email="admin@example.test", password_hash=hash_password("admin-password-123"), role="admin"),
                            User(email="viewer@example.test", password_hash=hash_password("viewer-password-123"), role="viewer")])
        db.session.commit()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_protected_routes_and_secure_login(client, app):
    assert client.get("/login").status_code == 200
    assert client.get("/api/summary").status_code == 401
    assert login(client, "admin@example.test", "wrong-password").status_code == 401
    assert login(client, "admin@example.test", "admin-password-123").status_code == 200
    assert client.get("/api/auth/me").get_json()["role"] == "admin"
    with app.app_context():
        assert User.query.filter_by(email="admin@example.test").first().password_hash != "admin-password-123"
        assert AuditEvent.query.filter_by(action="login").count() == 1


def test_role_enforcement(client):
    assert login(client, "viewer@example.test", "viewer-password-123").status_code == 200
    assert client.post("/api/rules/1/run").status_code == 403
    assert client.get("/api/reports/alarms.csv").status_code == 403
    assert client.get("/api/summary").status_code == 200


def test_audit_notification_and_csv_report(client, app):
    login(client, "admin@example.test", "admin-password-123")
    result = client.post("/api/rules/1/run")
    assert result.status_code == 200
    assert result.get_json()["matched_records"] == 1
    report = client.get("/api/reports/alarms.csv")
    assert report.status_code == 200
    assert report.mimetype == "text/csv"
    assert b"Large item" in report.data
    with app.app_context():
        assert Alarm.query.count() == 1
        assert Notification.query.filter_by(status="delivered").count() == 1
        assert AuditEvent.query.filter_by(action="rule_run").count() == 1


def test_admin_can_create_user_with_password_policy(client):
    login(client, "admin@example.test", "admin-password-123")
    weak = client.post("/api/users", json={"email": "auditor@example.test", "password": "short", "role": "auditor"})
    assert weak.status_code == 400
    created = client.post("/api/users", json={"email": "auditor@example.test",
                                               "password": "auditor-password-123", "role": "auditor"})
    assert created.status_code == 201
    assert created.get_json()["role"] == "auditor"
