"""Atomic, idempotent full-refresh orchestration for data sources."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import timedelta

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from connectors.base import FetchResult, SnapshotConnector, SourceFetchError
from models import (DataSnapshot, DataSource, DataSourceSyncPolicy, DataSourceSyncRun,
                    db, utcnow)
from postgres_connector import ConnectorError, PostgresConnector


class SyncConflict(RuntimeError):
    """Raised when another worker owns the source refresh lock."""


class PostgresRefreshConnector:
    def __init__(self, connector=None):
        self.connector = connector or PostgresConnector()

    def fetch_full(self, source: DataSource, max_records: int) -> FetchResult:
        config = source.config or {}
        required = ("profile", "schema", "table")
        if any(not config.get(key) for key in required):
            raise SourceFetchError("PostgreSQL source profile metadata is incomplete")
        try:
            records, truncated = self.connector.select_rows(
                config["profile"], config["schema"], config["table"], max_records)
            if truncated:
                raise SourceFetchError("source exceeds the configured full-refresh record limit")
            columns = self.connector.discover_columns(
                config["profile"], config["schema"], config["table"])
            return FetchResult(records=records, columns=columns)
        except ConnectorError as exc:
            raise SourceFetchError(str(exc)) from exc


def ensure_sync_policy(source: DataSource) -> DataSourceSyncPolicy:
    policy = DataSourceSyncPolicy.query.filter_by(data_source_id=source.id).first()
    if policy:
        return policy
    try:
        policy = DataSourceSyncPolicy(data_source_id=source.id)
        db.session.add(policy)
        db.session.commit()
        return policy
    except IntegrityError:
        db.session.rollback()
        return DataSourceSyncPolicy.query.filter_by(data_source_id=source.id).one()


def _acquire_lock(policy: DataSourceSyncPolicy, now, lock_seconds: int) -> str:
    token = str(uuid.uuid4())
    updated = DataSourceSyncPolicy.query.filter(
        DataSourceSyncPolicy.id == policy.id,
        or_(DataSourceSyncPolicy.lock_token.is_(None), DataSourceSyncPolicy.lock_until < now),
    ).update({DataSourceSyncPolicy.lock_token: token,
              DataSourceSyncPolicy.lock_until: now + timedelta(seconds=lock_seconds)},
             synchronize_session=False)
    db.session.commit()
    if updated != 1:
        raise SyncConflict("a synchronization is already running for this source")
    return token


def _release_lock(policy_id: int, token: str) -> None:
    DataSourceSyncPolicy.query.filter_by(id=policy_id, lock_token=token).update(
        {DataSourceSyncPolicy.lock_token: None, DataSourceSyncPolicy.lock_until: None},
        synchronize_session=False)


def _checksum(result: FetchResult) -> str:
    payload = json.dumps({"columns": result.columns, "records": result.records},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class FullRefreshService:
    def __init__(self, connectors=None, lock_seconds: int = 300):
        self.connectors = connectors or {
            "synthetic": SnapshotConnector(), "csv": SnapshotConnector(),
            "xlsx": SnapshotConnector(), "sqlite": SnapshotConnector(),
            "postgresql": PostgresRefreshConnector(),
        }
        self.lock_seconds = max(30, min(int(lock_seconds), 1800))

    def synchronize(self, source: DataSource, idempotency_key: str) -> tuple[DataSourceSyncRun, bool]:
        key = (idempotency_key or "").strip()
        if not key or len(key) > 128:
            raise ValueError("Idempotency-Key must contain 1-128 characters")
        existing = DataSourceSyncRun.query.filter_by(
            data_source_id=source.id, idempotency_key=key).first()
        if existing:
            return existing, True

        policy = ensure_sync_policy(source)
        if not policy.is_enabled:
            raise SyncConflict("synchronization is disabled for this source")
        token = _acquire_lock(policy, utcnow(), self.lock_seconds)
        try:
            run = DataSourceSyncRun(data_source_id=source.id, idempotency_key=key, status="running")
            db.session.add(run)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            _release_lock(policy.id, token)
            db.session.commit()
            existing = DataSourceSyncRun.query.filter_by(
                data_source_id=source.id, idempotency_key=key).one()
            return existing, True

        try:
            connector = self.connectors.get(source.source_type)
            if not connector:
                raise SourceFetchError("source type does not support full-refresh synchronization")
            result = connector.fetch_full(source, policy.max_records)
            if len(result.records) > policy.max_records:
                raise SourceFetchError("source exceeds the configured full-refresh record limit")

            finished = utcnow()
            next_version = (db.session.query(func.coalesce(func.max(DataSnapshot.version), 0))
                            .filter(DataSnapshot.data_source_id == source.id).scalar() + 1)
            DataSnapshot.query.filter_by(data_source_id=source.id, status="active").update(
                {DataSnapshot.status: "superseded"}, synchronize_session=False)
            snapshot = DataSnapshot(data_source_id=source.id, version=next_version, status="active",
                                    row_count=len(result.records), schema_json=result.columns,
                                    content_checksum=_checksum(result), activated_at=finished)
            db.session.add(snapshot)
            db.session.flush()
            current_config = dict(source.config or {})
            current_config.update({"records": result.records, "columns": result.columns,
                                   "active_snapshot_id": snapshot.id})
            source.config = current_config
            source.last_sync = finished
            run.snapshot_id = snapshot.id
            run.status = "succeeded"
            run.records_fetched = len(result.records)
            run.finished_at = finished
            _release_lock(policy.id, token)
            db.session.commit()
            return run, False
        except Exception:
            db.session.rollback()
            failed_run = db.session.get(DataSourceSyncRun, run.id)
            failed_run.status = "failed"
            failed_run.error_message = "source refresh failed"
            failed_run.finished_at = utcnow()
            _release_lock(policy.id, token)
            db.session.commit()
            return failed_run, False
