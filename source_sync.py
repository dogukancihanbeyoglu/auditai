"""RBAC-protected source synchronization API."""

import uuid

from flask import Blueprint, current_app, jsonify, request

from models import DataSource, DataSourceSyncPolicy, DataSourceSyncRun, db
from security import record_event, require_role
from services.source_sync import FullRefreshService, SyncConflict, ensure_sync_policy


source_sync_bp = Blueprint("source_sync", __name__)


def _service():
    factory = current_app.config.get("SOURCE_SYNC_SERVICE_FACTORY", FullRefreshService)
    return factory()


def _run_json(run: DataSourceSyncRun) -> dict:
    return {"id": run.id, "data_source_id": run.data_source_id, "snapshot_id": run.snapshot_id,
            "idempotency_key": run.idempotency_key, "status": run.status,
            "records_fetched": run.records_fetched, "error_message": run.error_message,
            "started_at": run.started_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None}


def _policy_json(policy: DataSourceSyncPolicy) -> dict:
    return {"data_source_id": policy.data_source_id, "is_enabled": policy.is_enabled,
            "refresh_mode": policy.refresh_mode, "max_records": policy.max_records,
            "locked": bool(policy.lock_token)}


@source_sync_bp.post("/api/data-sources/<int:source_id>/sync")
@require_role("auditor")
def synchronize_source(source_id):
    source = db.get_or_404(DataSource, source_id)
    key = request.headers.get("Idempotency-Key") or str(uuid.uuid4())
    try:
        run, replayed = _service().synchronize(source, key)
        action = ("data_source_sync_replayed" if replayed else
                  "data_source_sync_completed" if run.status == "succeeded" else "data_source_sync_failed")
        record_event(action,
                     "data_source", source.id, {"run_id": run.id, "status": run.status})
        db.session.commit()
        status_code = 200 if replayed else 201 if run.status == "succeeded" else 502
        return jsonify(**_run_json(run), replayed=replayed), status_code
    except (SyncConflict, ValueError) as exc:
        record_event("data_source_sync_rejected", "data_source", source.id, {"reason": str(exc)})
        db.session.commit()
        return jsonify(error=str(exc)), 409 if isinstance(exc, SyncConflict) else 400


@source_sync_bp.get("/api/data-sources/<int:source_id>/sync-runs")
@require_role()
def list_sync_runs(source_id):
    db.get_or_404(DataSource, source_id)
    runs = DataSourceSyncRun.query.filter_by(data_source_id=source_id).order_by(
        DataSourceSyncRun.started_at.desc()).limit(100).all()
    return jsonify([_run_json(run) for run in runs])


@source_sync_bp.patch("/api/data-sources/<int:source_id>/sync-policy")
@require_role("auditor")
def update_sync_policy(source_id):
    source = db.get_or_404(DataSource, source_id)
    payload = request.get_json(silent=True) or {}
    policy = ensure_sync_policy(source)
    try:
        if "is_enabled" in payload:
            if not isinstance(payload["is_enabled"], bool):
                raise ValueError("is_enabled must be boolean")
            policy.is_enabled = payload["is_enabled"]
        if "refresh_mode" in payload and payload["refresh_mode"] != "full":
            raise ValueError("only full refresh is currently supported")
        if "max_records" in payload:
            maximum = int(payload["max_records"])
            if not 1 <= maximum <= 10_000:
                raise ValueError("max_records must be between 1 and 10000")
            policy.max_records = maximum
        record_event("data_source_sync_policy_updated", "data_source", source.id,
                     {"is_enabled": policy.is_enabled, "max_records": policy.max_records})
        db.session.commit()
        return jsonify(_policy_json(policy))
    except (TypeError, ValueError) as exc:
        db.session.rollback()
        return jsonify(error=str(exc)), 400
