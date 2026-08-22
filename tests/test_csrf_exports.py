import csv
import io

import pytest

from app import create_app
from models import Alarm, AuditArea, AuditEvent, AuditRule, DataSource, User, db
from security import hash_password


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "CSRF_ENABLED": True, "SECRET_KEY": "csrf-test-secret",
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'csrf.db'}"})
    with application.app_context():
        area = AuditArea(name="=HYPERLINK(\"https://invalid\")")
        source = DataSource(name="Ledger", audit_area=area, config={"records": []})
        rule = AuditRule(name="+Malicious formula", field_name="amount", operator=">", threshold_value=10,
                         severity="high", audit_area=area, data_source=source)
        alarm = Alarm(title="@SUM(1+1)", message="test", severity="high", affected_records=[],
                      rule=rule, audit_area=area, data_source=source)
        user = User(email="admin@test.invalid", password_hash=hash_password("admin-password-123"), role="admin")
        db.session.add_all([area, source, rule, alarm, user])
        db.session.commit()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf_headers(client, **extra):
    token = client.get("/api/auth/csrf").get_json()["csrf_token"]
    return {"X-CSRF-Token": token, **extra}


def login(client):
    return client.post("/api/auth/login", json={"email": "admin@test.invalid", "password": "admin-password-123"},
                       headers=csrf_headers(client, Origin="http://localhost"))


def test_login_is_csrf_protected_and_templates_publish_token(client):
    payload = {"email": "admin@test.invalid", "password": "admin-password-123"}
    assert client.post("/api/auth/login", json=payload).status_code == 403
    login_page = client.get("/login")
    assert b'name="csrf-token"' in login_page.data
    assert b"X-CSRF-Token" in login_page.data
    assert login(client).status_code == 200
    assert b'name="csrf-token"' in client.get("/").data


def test_all_mutations_require_current_session_token(client):
    assert login(client).status_code == 200
    payload = {"email": "viewer@test.invalid", "password": "viewer-password-123", "role": "viewer"}
    assert client.post("/api/users", json=payload).status_code == 403
    valid = csrf_headers(client, Origin="http://localhost")
    assert client.post("/api/users", json=payload, headers=valid).status_code == 201
    assert client.post("/api/auth/logout", headers=valid).status_code == 204


def test_cross_origin_is_rejected_even_with_valid_token(client):
    headers = csrf_headers(client, Origin="https://attacker.invalid")
    response = client.post("/api/auth/login", json={"email": "admin@test.invalid", "password": "admin-password-123"},
                           headers=headers)
    assert response.status_code == 403
    assert "cross-origin" in response.get_json()["error"]


def test_sec_fetch_site_cross_site_is_rejected_without_origin(client):
    headers = csrf_headers(client, **{"Sec-Fetch-Site": "cross-site"})
    response = client.post("/api/auth/login", json={}, headers=headers)
    assert response.status_code == 403
    assert "cross-origin" in response.get_json()["error"]


def test_csv_cells_are_formula_safe_and_export_is_audited(client, app):
    assert login(client).status_code == 200
    response = client.get("/api/reports/alarms.csv?status=open")
    assert response.status_code == 200
    rows = list(csv.reader(io.StringIO(response.get_data(as_text=True))))
    assert rows[1][1].startswith("'@")
    assert rows[1][4].startswith("'+")
    assert rows[1][5].startswith("'=")
    with app.app_context():
        event = AuditEvent.query.filter_by(action="report_exported").one()
        assert event.actor.email == "admin@test.invalid"
        assert event.details == {"format": "csv", "filters": {"status": "open"}}
