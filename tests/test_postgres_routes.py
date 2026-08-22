import pytest

from app import create_app
from models import AuditArea, DataSource, db


class FakeConnector:
    def discover_tables(self, profile):
        return [{"schema": "public", "table": "invoices"}]

    def discover_columns(self, profile, schema, table):
        return [{"name": "id", "declared_type": "integer", "nullable": False,
                 "ordinal_position": 1},
                {"name": "amount", "declared_type": "numeric", "nullable": True,
                 "ordinal_position": 2}]

    def select_rows(self, profile, schema, table, limit):
        return ([{"id": 1, "amount": 125.0}, {"id": 2, "amount": 900.0}], False)


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "AUTH_REQUIRED": False,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'app.db'}",
        "POSTGRES_CONNECTOR_FACTORY": FakeConnector})
    with application.app_context():
        db.session.add(AuditArea(name="Finance"))
        db.session.commit()
    return application


def test_discovery_and_import_never_persist_dsn(app):
    client = app.test_client()
    tested = client.get("/api/connectors/postgresql/finance/test")
    assert tested.status_code == 200
    assert tested.get_json()["table_count"] == 1
    assert client.get("/api/connectors/postgresql/finance/tables").get_json()["tables"] == [
        {"schema": "public", "table": "invoices"}]
    columns = client.get(
        "/api/connectors/postgresql/finance/columns?schema=public&table=invoices"
    ).get_json()["columns"]
    assert [item["name"] for item in columns] == ["id", "amount"]
    preview = client.get(
        "/api/connectors/postgresql/finance/preview?schema=public&table=invoices&limit=1"
    )
    assert preview.status_code == 200
    assert preview.get_json()["records"][0] == {"id": 1, "amount": 125.0}

    response = client.post("/api/data-sources/postgresql", json={"profile": "finance",
        "schema": "public", "table": "invoices", "audit_area_id": 1, "limit": 100})
    assert response.status_code == 201
    assert response.get_json()["record_count"] == 2
    with app.app_context():
        source = DataSource.query.one()
        assert source.source_type == "postgresql"
        assert source.config["profile"] == "finance"
        assert "dsn" not in source.config
        assert "password" not in source.config


def test_import_validates_required_fields(app):
    response = app.test_client().post("/api/data-sources/postgresql", json={"profile": "finance"})
    assert response.status_code == 400
    assert "required" in response.get_json()["error"]
