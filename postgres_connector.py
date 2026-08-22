"""Read-only PostgreSQL discovery and bounded snapshot ingestion."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from contextlib import contextmanager
from typing import Any, Callable

import psycopg
from psycopg import sql


PROFILE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,31}$")
DEFAULT_SCHEMA_ALLOWLIST = ("public",)


class ConnectorError(RuntimeError):
    """Safe, user-facing connector error that never includes a DSN."""


class PostgresConnector:
    def __init__(self, environ: Mapping[str, str] | None = None,
                 connect: Callable[..., Any] | None = None, statement_timeout_ms: int = 5_000):
        self.environ = environ if environ is not None else os.environ
        self.connect = connect or psycopg.connect
        self.statement_timeout_ms = max(100, min(int(statement_timeout_ms), 60_000))

    def _profile_key(self, profile: str) -> str:
        if not PROFILE_PATTERN.fullmatch(profile or ""):
            raise ConnectorError("invalid PostgreSQL connection profile")
        return f"AUDITAI_SOURCE_{profile.upper()}_DSN"

    def resolve_dsn(self, profile: str) -> str:
        dsn = self.environ.get(self._profile_key(profile), "").strip()
        if not dsn:
            raise ConnectorError("PostgreSQL connection profile is not configured")
        if not dsn.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
            raise ConnectorError("PostgreSQL profile must contain a PostgreSQL DSN")
        return dsn.replace("postgresql+psycopg://", "postgresql://", 1)

    @contextmanager
    def connection(self, profile: str):
        dsn = self.resolve_dsn(profile)
        try:
            with self.connect(dsn, connect_timeout=5,
                              options="-c default_transaction_read_only=on") as connection:
                with connection.transaction():
                    connection.execute("SET LOCAL statement_timeout = %s", (self.statement_timeout_ms,))
                    yield connection
        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError("PostgreSQL source operation failed") from exc

    def allowed_schemas(self) -> tuple[str, ...]:
        configured = self.environ.get("AUDITAI_POSTGRES_SCHEMAS", "").strip()
        if not configured:
            return DEFAULT_SCHEMA_ALLOWLIST
        schemas = tuple(dict.fromkeys(item.strip() for item in configured.split(",") if item.strip()))
        if not schemas or any(not PROFILE_PATTERN.fullmatch(item) for item in schemas):
            raise ConnectorError("invalid PostgreSQL schema allowlist")
        return schemas

    def discover_tables(self, profile: str) -> list[dict[str, str]]:
        schemas = self.allowed_schemas()
        with self.connection(profile) as connection:
            rows = connection.execute(
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_type = 'BASE TABLE' AND table_schema = ANY(%s) "
                "ORDER BY table_schema, table_name", (list(schemas),)
            ).fetchall()
        return [{"schema": row[0], "table": row[1]} for row in rows]

    def discover_columns(self, profile: str, schema_name: str, table_name: str) -> list[dict[str, Any]]:
        self._require_allowed_table(profile, schema_name, table_name)
        with self.connection(profile) as connection:
            rows = connection.execute(
                "SELECT column_name, data_type, is_nullable, ordinal_position "
                "FROM information_schema.columns WHERE table_schema = %s AND table_name = %s "
                "ORDER BY ordinal_position", (schema_name, table_name)
            ).fetchall()
        return [{"name": row[0], "declared_type": row[1], "nullable": row[2] == "YES",
                 "ordinal_position": row[3]} for row in rows]

    def _require_allowed_table(self, profile: str, schema_name: str, table_name: str) -> None:
        if schema_name not in self.allowed_schemas():
            raise ConnectorError("schema is not allowlisted")
        tables = {(item["schema"], item["table"]) for item in self.discover_tables(profile)}
        if (schema_name, table_name) not in tables:
            raise ConnectorError("table is not available in the source allowlist")

    def select_rows(self, profile: str, schema_name: str, table_name: str,
                    limit: int) -> tuple[list[dict[str, Any]], bool]:
        bounded_limit = max(1, min(int(limit), 10_000))
        self._require_allowed_table(profile, schema_name, table_name)
        statement = sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(
            sql.Identifier(schema_name), sql.Identifier(table_name)
        )
        with self.connection(profile) as connection:
            cursor = connection.execute(statement, (bounded_limit + 1,))
            names = [column.name for column in cursor.description]
            rows = cursor.fetchall()
        truncated = len(rows) > bounded_limit
        records = [{name: _json_value(value) for name, value in zip(names, row)}
                   for row in rows[:bounded_limit]]
        return records, truncated


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray, memoryview)):
        return bytes(value).hex()
    return str(value)
