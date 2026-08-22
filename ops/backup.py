"""Safe SQLite backup and recovery CLI for local/demo deployments."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile


def _validate_database(path: Path, *, must_exist=True) -> Path:
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise ValueError("database cannot be a symlink")
    resolved = expanded.resolve()
    if must_exist and not resolved.is_file():
        raise ValueError("database must be an existing regular file")
    return resolved


def _integrity_check(path: Path) -> None:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        connection.close()
    if result != "ok":
        raise ValueError(f"SQLite integrity check failed: {result}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def backup_sqlite(database: Path, output_dir: Path, *, now=None) -> tuple[Path, Path]:
    source = _validate_database(database)
    expanded_dir = output_dir.expanduser()
    if expanded_dir.is_symlink():
        raise ValueError("output directory cannot be a symlink")
    destination_dir = expanded_dir.resolve()
    destination_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    destination = destination_dir / f"auditai-{stamp}.sqlite3"
    if destination.exists():
        raise FileExistsError(f"backup already exists: {destination}")
    with tempfile.NamedTemporaryFile(dir=destination_dir, prefix=".backup-", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as src, sqlite3.connect(temporary) as dst:
            src.backup(dst)
        _integrity_check(temporary)
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    manifest = destination.with_suffix(".json")
    manifest.write_text(json.dumps({
        "format": "auditai-sqlite-backup-v1", "created_at": (now or datetime.now(timezone.utc)).isoformat(),
        "filename": destination.name, "bytes": destination.stat().st_size, "sha256": _sha256(destination),
    }, indent=2) + "\n", encoding="utf-8")
    os.chmod(manifest, 0o600)
    return destination, manifest


def verify_manifest(backup: Path, manifest: Path) -> None:
    source = _validate_database(backup)
    metadata = json.loads(manifest.read_text(encoding="utf-8"))
    if metadata.get("format") != "auditai-sqlite-backup-v1" or metadata.get("filename") != source.name:
        raise ValueError("backup manifest identity mismatch")
    if metadata.get("bytes") != source.stat().st_size or metadata.get("sha256") != _sha256(source):
        raise ValueError("backup manifest checksum mismatch")


def restore_sqlite(backup: Path, database: Path, *, manifest: Path, confirm_target: str) -> Path | None:
    source = _validate_database(backup)
    verify_manifest(source, manifest)
    target = database.expanduser().resolve()
    if confirm_target != str(target):
        raise ValueError("confirm_target must exactly match the resolved database path")
    _integrity_check(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    recovery_copy = None
    if target.exists():
        _validate_database(target)
        recovery_copy = target.with_name(f"{target.name}.pre-restore")
        if recovery_copy.exists():
            raise FileExistsError(f"recovery copy already exists: {recovery_copy}")
        with sqlite3.connect(f"file:{target}?mode=ro", uri=True) as src, sqlite3.connect(recovery_copy) as dst:
            src.backup(dst)
        os.chmod(recovery_copy, 0o600)
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".restore-", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as src, sqlite3.connect(temporary) as dst:
            src.backup(dst)
        _integrity_check(temporary)
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return recovery_copy


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    backup = commands.add_parser("backup")
    backup.add_argument("--database", type=Path, required=True)
    backup.add_argument("--output-dir", type=Path, required=True)
    restore = commands.add_parser("restore")
    restore.add_argument("--backup", type=Path, required=True)
    restore.add_argument("--manifest", type=Path, required=True)
    restore.add_argument("--database", type=Path, required=True)
    restore.add_argument("--confirm-target", required=True)
    args = parser.parse_args(argv)
    if args.command == "backup":
        destination, manifest = backup_sqlite(args.database, args.output_dir)
        print(json.dumps({"backup": str(destination), "manifest": str(manifest)}))
    else:
        recovery = restore_sqlite(args.backup, args.database, manifest=args.manifest, confirm_target=args.confirm_target)
        print(json.dumps({"restored": str(args.database.resolve()), "recovery_copy": str(recovery) if recovery else None}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
