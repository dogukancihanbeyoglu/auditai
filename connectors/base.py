"""Connector protocol for bounded full-refresh synchronization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from models import DataSource


class SourceFetchError(RuntimeError):
    """A redacted source-fetch failure safe to persist and return."""


@dataclass(frozen=True)
class FetchResult:
    records: list[dict[str, Any]]
    columns: list[dict[str, Any]]


class SourceConnector(Protocol):
    def fetch_full(self, source: DataSource, max_records: int) -> FetchResult:
        """Return one complete bounded snapshot or raise without mutating the source."""


class SnapshotConnector:
    """Re-snapshots already persisted synthetic/file/SQLite records safely."""

    def fetch_full(self, source: DataSource, max_records: int) -> FetchResult:
        config = source.config or {}
        records = list(config.get("records", []))
        if len(records) > max_records:
            raise SourceFetchError("source exceeds the configured full-refresh record limit")
        if any(not isinstance(record, dict) for record in records):
            raise SourceFetchError("source contains invalid persisted records")
        return FetchResult(records=[dict(record) for record in records],
                           columns=[dict(column) for column in config.get("columns", [])])
