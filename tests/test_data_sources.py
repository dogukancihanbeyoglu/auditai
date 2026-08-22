import io
import sqlite3

import pytest
from openpyxl import Workbook

from app import create_app
from models import AuditArea, DataSnapshot, DataSource, DataSourceArtifact, db
from services.source_sync import FullRefreshService


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True,
                              "AUTH_REQUIRED": False,
                              "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'app.db'}",
                              "SOURCE_MAX_BYTES": 1024 * 1024})
    with application.app_context():
        db.session.add(AuditArea(name="Data tests"))
        db.session.commit()
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def _xlsx_bytes():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Invoices"
    sheet.append(["invoice_id", "amount", "paid_at"])
    sheet.append(["INV-1", 125.5, None])
    stream = io.BytesIO()
    workbook.save(stream)
    workbook.close()
    return stream.getvalue()


def _sqlite_bytes(tmp_path):
    path = tmp_path / "source.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE payments (id INTEGER PRIMARY KEY, vendor TEXT, amount REAL)")
    connection.executemany("INSERT INTO payments(vendor, amount) VALUES (?, ?)",
                           [("Atlas", 50), ("Contoso", 250)])
    connection.commit()
    connection.close()
    return path.read_bytes()


def test_csv_upload_schema_preview_and_rule_compatibility(client):
    response = client.post("/api/data-sources/upload", data={
        "audit_area_id": "1", "name": "Invoice CSV",
        "file": (io.BytesIO(b"id,amount,vendor\n1,50,Atlas\n2,250,Contoso\n"), "invoices.csv"),
    }, content_type="multipart/form-data")
    assert response.status_code == 201
    body = response.get_json()
    assert body["record_count"] == 2
    assert [column["name"] for column in body["columns"]] == ["id", "amount", "vendor"]

    schema = client.get(f"/api/data-sources/{body['source_id']}/schema").get_json()
    assert schema["source_type"] == "csv"
    preview = client.get(f"/api/data-sources/{body['source_id']}/preview?limit=1").get_json()
    assert preview["total_records"] == 2
    assert preview["records"] == [{"amount": "50", "id": "1", "vendor": "Atlas"}]

    rule = client.post("/api/rules", json={"name": "Large invoice", "field_name": "amount",
        "operator": ">", "threshold_value": 100, "severity": "high",
        "audit_area_id": 1, "data_source_id": body["source_id"]})
    assert rule.status_code == 201
    result = client.post(f"/api/rules/{rule.get_json()['id']}/run").get_json()
    assert result["scanned_records"] == 2
    assert result["matched_records"] == 1


def test_xlsx_upload_selects_sheet(client):
    response = client.post("/api/data-sources/upload", data={
        "audit_area_id": "1", "sheet_name": "Invoices",
        "file": (io.BytesIO(_xlsx_bytes()), "invoices.xlsx"),
    }, content_type="multipart/form-data")
    assert response.status_code == 201
    body = response.get_json()
    assert body["source_type"] == "xlsx"
    assert body["preview"][0]["amount"] == 125.5
    schema = client.get(f"/api/data-sources/{body['source_id']}/schema").get_json()
    assert schema["sheet_name"] == "Invoices"


def test_sqlite_upload_discovers_tables_and_columns(client, tmp_path):
    response = client.post("/api/data-sources/sqlite", data={
        "audit_area_id": "1", "table_name": "payments",
        "file": (io.BytesIO(_sqlite_bytes(tmp_path)), "ledger.db"),
    }, content_type="multipart/form-data")
    assert response.status_code == 201
    body = response.get_json()
    assert body["available_tables"] == ["payments"]
    assert body["table_name"] == "payments"
    assert body["record_count"] == 2
    assert body["preview"][1]["vendor"] == "Contoso"
    assert any(column["primary_key"] for column in body["columns"])


@pytest.mark.parametrize(("filename", "content", "endpoint", "expected"), [
    ("data.txt", b"id,value\n1,2\n", "/api/data-sources/upload", "only CSV and XLSX"),
    ("fake.db", b"not sqlite", "/api/data-sources/sqlite", "not a SQLite"),
])
def test_rejects_unsupported_or_invalid_files(client, filename, content, endpoint, expected):
    response = client.post(endpoint, data={"audit_area_id": "1",
        "file": (io.BytesIO(content), filename)}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert expected in response.get_json()["error"]


def test_rejects_unknown_sqlite_table(client, tmp_path):
    response = client.post("/api/data-sources/sqlite", data={
        "audit_area_id": "1", "table_name": "payments; DROP TABLE payments",
        "file": (io.BytesIO(_sqlite_bytes(tmp_path)), "ledger.db"),
    }, content_type="multipart/form-data")
    assert response.status_code == 400
    assert response.get_json()["error"] == "requested table does not exist"


def test_csv_upload_reload_versions_artifact_and_snapshot(app, client):
    first_bytes = b"id,amount\n1,50\n"
    first = client.post("/api/data-sources/upload", data={"audit_area_id": "1",
        "name": "Reloadable", "file": (io.BytesIO(first_bytes), "ledger.csv")},
        content_type="multipart/form-data")
    assert first.status_code == 201
    source_id = first.get_json()["source_id"]
    assert first.get_json()["artifact_version"] == 1
    assert len(first.get_json()["checksum"]) == 64

    second_bytes = b"id,amount\n1,75\n2,250\n"
    second = client.post(f"/api/data-sources/{source_id}/reload", data={
        "file": (io.BytesIO(second_bytes), "ledger-v2.csv")}, content_type="multipart/form-data")
    assert second.status_code == 201
    assert second.get_json()["artifact_version"] == 2
    assert second.get_json()["record_count"] == 2
    duplicate = client.post(f"/api/data-sources/{source_id}/reload", data={
        "file": (io.BytesIO(second_bytes), "copy.csv")}, content_type="multipart/form-data")
    assert duplicate.status_code == 409

    with app.app_context():
        source = db.session.get(DataSource, source_id)
        assert source.config["records"][1]["amount"] == "250"
        assert [item.version for item in source.artifacts] == [1, 2]
        assert [item.status for item in DataSnapshot.query.filter_by(
            data_source_id=source_id).order_by(DataSnapshot.version)] == ["superseded", "active"]
        assert all(len(item.content_checksum) == 64 for item in DataSourceArtifact.query.all())


def test_file_sync_reloads_from_immutable_artifact_instead_of_mutated_snapshot(app, client):
    response = client.post("/api/data-sources/upload", data={"audit_area_id": "1",
        "file": (io.BytesIO(b"id,amount\n1,50\n"), "ledger.csv")},
        content_type="multipart/form-data")
    source_id = response.get_json()["source_id"]
    with app.app_context():
        source = db.session.get(DataSource, source_id)
        source.config = {**source.config, "records": [{"tampered": True}]}
        db.session.commit()
        run, _ = FullRefreshService().synchronize(source, "artifact-refresh")
        assert run.status == "succeeded"
        assert db.session.get(DataSource, source_id).config["records"] == [{"id": "1", "amount": "50"}]


def test_sqlite_connector_test_discovery_and_preview(client, tmp_path):
    content = _sqlite_bytes(tmp_path)
    tested = client.post("/api/connectors/sqlite/test", data={
        "file": (io.BytesIO(content), "ledger.db")}, content_type="multipart/form-data")
    assert tested.status_code == 200
    assert tested.get_json()["status"] == "ok"
    discovered = client.post("/api/connectors/sqlite/tables", data={
        "file": (io.BytesIO(content), "ledger.db")}, content_type="multipart/form-data")
    assert discovered.get_json()["tables"] == ["payments"]
    preview = client.post("/api/connectors/sqlite/preview", data={"table_name": "payments", "limit": "1",
        "file": (io.BytesIO(content), "ledger.db")}, content_type="multipart/form-data")
    assert preview.status_code == 200
    assert preview.get_json()["total_records"] == 2
    assert preview.get_json()["records"] == [{"id": 1, "vendor": "Atlas", "amount": 50.0}]
