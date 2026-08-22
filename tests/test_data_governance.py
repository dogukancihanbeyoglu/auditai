import pytest
from flask import Flask

from data_governance import data_governance_bp
from models import AuditArea, DataSource, FieldMapping, QualityCheck, QualityCheckRun, db


@pytest.fixture()
def app(tmp_path):
    application = Flask(__name__)
    application.config.update(TESTING=True, AUTH_REQUIRED=False,
        SECRET_KEY="test-only", SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'governance.db'}")
    db.init_app(application)
    application.register_blueprint(data_governance_bp)
    with application.app_context():
        db.create_all()
        area = AuditArea(name="Finance")
        source = DataSource(name="Invoices", audit_area=area, config={
            "columns": [{"name": "invoice_id"}, {"name": "vendor"}, {"name": "amount"}],
            "records": [
                {"invoice_id": "INV-1", "vendor": "Atlas", "amount": 50},
                {"invoice_id": "INV-2", "vendor": "", "amount": 250},
                {"invoice_id": "INV-2", "vendor": None, "amount": "bad"},
            ]})
        db.session.add_all([area, source])
        db.session.commit()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def test_mapping_crud_validates_persisted_schema(app, client):
    created = client.post("/api/data-sources/1/mappings", json={"source_column": "invoice_id",
        "target_field": "invoice_number", "target_type": "string", "transformation": "trim",
        "is_required": True})
    assert created.status_code == 201
    mapping = created.get_json()
    assert mapping["source_column"] == "invoice_id"
    assert mapping["target_field"] == "invoice_number"

    duplicate = client.post("/api/data-sources/1/mappings", json={
        "source_column": "invoice_id", "target_field": "invoice_number"})
    assert duplicate.status_code == 409
    invalid = client.post("/api/data-sources/1/mappings", json={
        "source_column": "not_a_column", "target_field": "anything"})
    assert invalid.status_code == 400

    updated = client.patch(f"/api/mappings/{mapping['id']}", json={"target_type": "integer",
                                                                    "transformation": "to_integer"})
    assert updated.status_code == 200
    assert updated.get_json()["target_type"] == "integer"
    assert len(client.get("/api/data-sources/1/mappings").get_json()) == 1
    with app.app_context():
        assert FieldMapping.query.one().is_required is True
    assert client.delete(f"/api/mappings/{mapping['id']}").status_code == 204


@pytest.mark.parametrize(("payload", "failed", "status"), [
    ({"name": "Vendor required", "check_type": "not_null", "field_name": "vendor"}, 2, "failed"),
    ({"name": "Unique invoice", "check_type": "unique", "field_name": "invoice_id"}, 2, "failed"),
    ({"name": "Amount bounds", "check_type": "numeric_range", "field_name": "amount",
      "parameters": {"min": 0, "max": 200}}, 2, "failed"),
    ({"name": "Known vendors", "check_type": "accepted_values", "field_name": "vendor",
      "parameters": {"values": ["Atlas", "Contoso"]}}, 2, "failed"),
])
def test_quality_checks_execute_against_persisted_records(app, client, payload, failed, status):
    created = client.post("/api/data-sources/1/quality-checks", json=payload)
    assert created.status_code == 201
    check_id = created.get_json()["id"]
    response = client.post(f"/api/quality-checks/{check_id}/run")
    assert response.status_code == 201
    run = response.get_json()
    assert run["scanned_records"] == 3
    assert run["failed_records"] == failed
    assert run["status"] == status
    assert len(run["failure_sample"]) == failed
    assert client.get(f"/api/quality-checks/{check_id}/runs").get_json()[0]["id"] == run["id"]
    with app.app_context():
        assert QualityCheck.query.one().last_run_at is not None
        assert QualityCheckRun.query.one().failed_records == failed


def test_quality_check_crud_and_parameter_validation(app, client):
    missing_range = client.post("/api/data-sources/1/quality-checks", json={
        "name": "Invalid range", "check_type": "numeric_range", "field_name": "amount"})
    assert missing_range.status_code == 400
    unknown_field = client.post("/api/data-sources/1/quality-checks", json={
        "name": "Unknown", "check_type": "not_null", "field_name": "missing"})
    assert unknown_field.status_code == 400

    created = client.post("/api/data-sources/1/quality-checks", json={
        "name": "Required vendor", "check_type": "not_null", "field_name": "vendor"}).get_json()
    updated = client.patch(f"/api/quality-checks/{created['id']}", json={"is_active": False})
    assert updated.status_code == 200
    assert client.post(f"/api/quality-checks/{created['id']}/run").status_code == 409
    assert len(client.get("/api/data-sources/1/quality-checks").get_json()) == 1
    assert client.delete(f"/api/quality-checks/{created['id']}").status_code == 204
    with app.app_context():
        assert QualityCheck.query.count() == 0
