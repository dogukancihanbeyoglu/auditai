import pytest
from flask import Flask

from audit_areas import audit_areas_bp
from models import AuditArea, AuditEvent, AuditRule, DataSource, User, db
from security import hash_password, security_bp


@pytest.fixture()
def app(tmp_path):
    application = Flask(__name__)
    application.config.update(TESTING=True, SECRET_KEY="test-only-secret", AUTH_REQUIRED=True,
                              SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'areas.db'}")
    db.init_app(application)
    application.register_blueprint(security_bp)
    application.register_blueprint(audit_areas_bp)
    with application.app_context():
        db.create_all()
        db.session.add_all([
            User(email="viewer@test.invalid", password_hash=hash_password("viewer-password-123"), role="viewer"),
            User(email="auditor@test.invalid", password_hash=hash_password("auditor-password-123"), role="auditor"),
            User(email="admin@test.invalid", password_hash=hash_password("admin-password-123"), role="admin"),
        ])
        db.session.commit()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, role):
    return client.post("/api/auth/login", json={"email": f"{role}@test.invalid", "password": f"{role}-password-123"})


def create(client, name="Payments", description="Payment controls"):
    return client.post("/api/audit-areas", json={"name": name, "description": description})


def test_authentication_and_roles(client):
    assert client.get("/api/audit-areas").status_code == 401
    login(client, "viewer")
    assert client.get("/api/audit-areas").status_code == 200
    assert create(client).status_code == 403
    assert client.delete("/api/audit-areas/1").status_code == 403


def test_full_create_list_detail_update_flow(client, app):
    login(client, "auditor")
    response = create(client)
    assert response.status_code == 201
    area_id = response.get_json()["id"]
    assert client.get(f"/api/audit-areas/{area_id}").get_json()["name"] == "Payments"
    updated = client.patch(f"/api/audit-areas/{area_id}", json={"name": "Accounts Payable", "description": "AP"})
    assert updated.status_code == 200
    assert updated.get_json()["name"] == "Accounts Payable"
    assert len(client.get("/api/audit-areas?q=payable&active=true").get_json()) == 1
    with app.app_context():
        assert AuditEvent.query.filter_by(action="audit_area_created").count() == 1
        assert AuditEvent.query.filter_by(action="audit_area_updated").count() == 1


@pytest.mark.parametrize("payload,error", [
    ({}, "name is required"),
    ({"name": "x" * 129}, "must not exceed"),
    ({"name": "Valid", "unexpected": True}, "unknown field"),
    ({"name": "Valid", "is_active": "yes"}, "must be a boolean"),
])
def test_create_validation(client, payload, error):
    login(client, "auditor")
    response = client.post("/api/audit-areas", json=payload)
    assert response.status_code == 400
    assert error in response.get_json()["error"]


def test_case_insensitive_uniqueness_and_patch_validation(client):
    login(client, "auditor")
    assert create(client).status_code == 201
    duplicate = create(client, " payments ")
    assert duplicate.status_code == 409
    assert client.patch("/api/audit-areas/1", json={}).status_code == 400
    assert client.patch("/api/audit-areas/1", json={"is_active": "false"}).status_code == 400


def test_deactivate_is_idempotent_and_audited(client, app):
    login(client, "auditor")
    area_id = create(client).get_json()["id"]
    assert client.post(f"/api/audit-areas/{area_id}/deactivate").get_json()["is_active"] is False
    assert client.post(f"/api/audit-areas/{area_id}/deactivate").get_json()["is_active"] is False
    assert client.get("/api/audit-areas?active=true").get_json() == []
    with app.app_context():
        assert AuditEvent.query.filter_by(action="audit_area_deactivated").count() == 2


def test_admin_delete_empty_area(client, app):
    login(client, "admin")
    area_id = create(client, "Empty area").get_json()["id"]
    assert client.delete(f"/api/audit-areas/{area_id}").status_code == 204
    assert client.get(f"/api/audit-areas/{area_id}").status_code == 404
    with app.app_context():
        assert AuditEvent.query.filter_by(action="audit_area_deleted").count() == 1


def test_linked_area_cannot_be_physically_deleted(client, app):
    login(client, "admin")
    area_id = create(client).get_json()["id"]
    with app.app_context():
        area = db.session.get(AuditArea, area_id)
        source = DataSource(name="Ledger", audit_area=area, config={"records": []})
        rule = AuditRule(name="Control", field_name="amount", operator=">", threshold_value=1,
                         severity="high", audit_area=area, data_source=source)
        db.session.add_all([source, rule])
        db.session.commit()
    response = client.delete(f"/api/audit-areas/{area_id}")
    assert response.status_code == 409
    assert response.get_json()["can_deactivate"] is True
    assert response.get_json()["dependencies"]["rules"] == 1
    with app.app_context():
        assert db.session.get(AuditArea, area_id) is not None
        assert AuditEvent.query.filter_by(action="audit_area_deleted").count() == 0
