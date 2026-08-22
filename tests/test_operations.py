from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

import pytest

from app import create_app
from ops.backup import backup_sqlite, restore_sqlite
from tools.performance_check import run_check
from worker import run_worker


def create_database(path: Path, value: str):
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE evidence (value TEXT)")
        connection.execute("INSERT INTO evidence VALUES (?)", (value,))


def read_value(path: Path) -> str:
    with sqlite3.connect(path) as connection:
        return connection.execute("SELECT value FROM evidence").fetchone()[0]


def test_backup_manifest_and_recoverable_restore(tmp_path):
    database = tmp_path / "auditai.db"
    create_database(database, "before")
    backup, manifest = backup_sqlite(database, tmp_path / "backups", now=datetime(2025, 1, 1, tzinfo=timezone.utc))
    metadata = json.loads(manifest.read_text())
    assert metadata["bytes"] == backup.stat().st_size
    assert len(metadata["sha256"]) == 64

    database.unlink()
    create_database(database, "after")
    recovery = restore_sqlite(backup, database, manifest=manifest, confirm_target=str(database.resolve()))
    assert read_value(database) == "before"
    assert recovery and read_value(recovery) == "after"


def test_restore_requires_exact_confirmation(tmp_path):
    database = tmp_path / "source.db"
    create_database(database, "safe")
    backup, manifest = backup_sqlite(database, tmp_path / "backups")
    with pytest.raises(ValueError, match="exactly match"):
        restore_sqlite(backup, tmp_path / "target.db", manifest=manifest, confirm_target="target.db")


def test_restore_rejects_tampered_backup(tmp_path):
    database = tmp_path / "source.db"
    create_database(database, "safe")
    backup, manifest = backup_sqlite(database, tmp_path / "backups")
    backup.write_bytes(backup.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="checksum mismatch"):
        restore_sqlite(backup, tmp_path / "target.db", manifest=manifest,
                       confirm_target=str((tmp_path / "target.db").resolve()))


def test_liveness_and_readiness_are_distinct(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'ready.db'}"})
    client = app.test_client()
    assert client.get("/health").get_json() == {"service": "auditai", "status": "ok"}
    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.get_json()["checks"]["schema"]["ready"] is True


def test_worker_once_and_performance_budget(tmp_path):
    factory = lambda: create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'worker.db'}"})
    assert run_worker(once=True, poll_seconds=5, app_factory=factory) == 0
    metrics = run_check(records=10_000, budget_ms=5000, memory_mb=64)
    assert metrics["passed"] is True
    assert metrics["records"] == 10_000
