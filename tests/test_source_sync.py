from datetime import timedelta

import pytest
from flask import Flask

from connectors.base import FetchResult, SourceFetchError
from models import (AuditArea, AuditEvent, DataSnapshot, DataSource, DataSourceSyncPolicy,
                    DataSourceSyncRun, User, db, utcnow)
from security import hash_password, security_bp
from services.source_sync import FullRefreshService
from source_sync import source_sync_bp


class SuccessfulConnector:
    def __init__(self):
        self.calls = 0

    def fetch_full(self, source, max_records):
        self.calls += 1
        return FetchResult(records=[{"id": 2, "amount": 250}],
                           columns=[{"name": "id"}, {"name": "amount"}])


class FailingConnector:
    def fetch_full(self, source, max_records):
        raise SourceFetchError("credential-containing internal failure")


@pytest.fixture()
def app(tmp_path):
    application = Flask(__name__)
    application.config.update(TESTING=True, AUTH_REQUIRED=False, SECRET_KEY="test-only",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'sync.db'}")
    db.init_app(application)
    application.register_blueprint(security_bp)
    application.register_blueprint(source_sync_bp)
    with application.app_context():
        db.create_all()
        area = AuditArea(name="Finance")
        source = DataSource(name="Ledger", source_type="synthetic", audit_area=area,
                            config={"records": [{"id": 1, "amount": 50}],
                                    "columns": [{"name": "id"}, {"name": "amount"}]})
        db.session.add_all([area, source])
        db.session.commit()
    return application


def test_successful_sync_atomically_activates_snapshot_and_is_idempotent(app):
    connector = SuccessfulConnector()
    app.config["SOURCE_SYNC_SERVICE_FACTORY"] = lambda: FullRefreshService(
        connectors={"synthetic": connector})
    client = app.test_client()

    first = client.post("/api/data-sources/1/sync", headers={"Idempotency-Key": "batch-2026-08-22"})
    assert first.status_code == 201
    assert first.get_json()["status"] == "succeeded"
    replay = client.post("/api/data-sources/1/sync", headers={"Idempotency-Key": "batch-2026-08-22"})
    assert replay.status_code == 200
    assert replay.get_json()["replayed"] is True
    assert replay.get_json()["id"] == first.get_json()["id"]
    assert connector.calls == 1

    with app.app_context():
        source = db.session.get(DataSource, 1)
        snapshot = DataSnapshot.query.one()
        assert source.config["records"] == [{"id": 2, "amount": 250}]
        assert source.config["active_snapshot_id"] == snapshot.id
        assert snapshot.status == "active"
        assert snapshot.row_count == 1
        assert len(snapshot.content_checksum) == 64
        assert DataSourceSyncRun.query.count() == 1
        assert AuditEvent.query.filter_by(action="data_source_sync_completed").count() == 1
        assert AuditEvent.query.filter_by(action="data_source_sync_replayed").count() == 1


def test_failed_refresh_preserves_previous_records_and_snapshot(app):
    with app.app_context():
        old = DataSnapshot(data_source_id=1, version=1, status="active", row_count=1,
                           schema_json=[{"name": "id"}], content_checksum="a" * 64)
        db.session.add(old)
        db.session.commit()
        old_id = old.id
    app.config["SOURCE_SYNC_SERVICE_FACTORY"] = lambda: FullRefreshService(
        connectors={"synthetic": FailingConnector()})

    response = app.test_client().post("/api/data-sources/1/sync",
                                      headers={"Idempotency-Key": "failed-refresh"})
    assert response.status_code == 502
    assert response.get_json()["status"] == "failed"
    assert response.get_json()["error_message"] == "source refresh failed"
    with app.app_context():
        source = db.session.get(DataSource, 1)
        assert source.config["records"] == [{"id": 1, "amount": 50}]
        assert DataSnapshot.query.count() == 1
        assert db.session.get(DataSnapshot, old_id).status == "active"
        assert DataSourceSyncRun.query.one().status == "failed"
        assert DataSourceSyncPolicy.query.one().lock_token is None
        assert AuditEvent.query.filter_by(action="data_source_sync_failed").count() == 1


def test_source_lock_rejects_parallel_sync(app):
    with app.app_context():
        db.session.add(DataSourceSyncPolicy(data_source_id=1, lock_token="another-worker",
                                           lock_until=utcnow() + timedelta(minutes=5)))
        db.session.commit()
    app.config["SOURCE_SYNC_SERVICE_FACTORY"] = lambda: FullRefreshService(
        connectors={"synthetic": SuccessfulConnector()})
    response = app.test_client().post("/api/data-sources/1/sync",
                                      headers={"Idempotency-Key": "parallel"})
    assert response.status_code == 409
    assert "already running" in response.get_json()["error"]
    with app.app_context():
        assert DataSourceSyncRun.query.count() == 0
        assert AuditEvent.query.filter_by(action="data_source_sync_rejected").count() == 1


def test_policy_crud_and_run_history(app):
    client = app.test_client()
    updated = client.patch("/api/data-sources/1/sync-policy",
                           json={"is_enabled": False, "max_records": 500})
    assert updated.status_code == 200
    assert updated.get_json()["is_enabled"] is False
    assert updated.get_json()["max_records"] == 500
    rejected = client.patch("/api/data-sources/1/sync-policy", json={"refresh_mode": "incremental"})
    assert rejected.status_code == 400
    assert client.get("/api/data-sources/1/sync-runs").get_json() == []


def test_sync_endpoints_require_auditor_role(tmp_path):
    application = Flask(__name__)
    application.config.update(TESTING=True, AUTH_REQUIRED=True, SECRET_KEY="test-only",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'rbac.db'}")
    db.init_app(application)
    application.register_blueprint(security_bp)
    application.register_blueprint(source_sync_bp)
    with application.app_context():
        db.create_all()
        area = AuditArea(name="Finance")
        source = DataSource(name="Ledger", audit_area=area, config={"records": []})
        viewer = User(email="viewer@example.test", password_hash=hash_password("viewer-password"),
                      role="viewer")
        db.session.add_all([area, source, viewer])
        db.session.commit()
    client = application.test_client()
    assert client.post("/api/data-sources/1/sync").status_code == 401
    assert client.post("/api/auth/login", json={"email": "viewer@example.test",
                                                "password": "viewer-password"}).status_code == 200
    assert client.get("/api/data-sources/1/sync-runs").status_code == 200
    assert client.post("/api/data-sources/1/sync").status_code == 403
    assert client.patch("/api/data-sources/1/sync-policy", json={"is_enabled": True}).status_code == 403
