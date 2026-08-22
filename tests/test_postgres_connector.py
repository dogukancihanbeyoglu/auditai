from types import SimpleNamespace

import pytest
from psycopg.sql import Composed

from postgres_connector import ConnectorError, PostgresConnector


class Result:
    def __init__(self, rows, names=()):
        self._rows = rows
        self.description = [SimpleNamespace(name=name) for name in names]

    def fetchall(self):
        return self._rows


class FakeConnection:
    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def transaction(self):
        return self

    def execute(self, statement, parameters=None):
        self.calls.append((statement, parameters))
        text = str(statement)
        if text.startswith("SET LOCAL"):
            return Result([])
        if "information_schema.tables" in text:
            return Result([("public", "invoices")])
        if "information_schema.columns" in text:
            return Result([("id", "integer", "NO", 1), ("amount", "numeric", "YES", 2)])
        if isinstance(statement, Composed):
            return Result([(1, 120.5), (2, 450.0), (3, 900.0)], ("id", "amount"))
        raise AssertionError(f"unexpected statement: {statement!r}")


def test_read_only_discovery_and_bounded_quoted_select():
    connection = FakeConnection()
    connect_calls = []

    def connect(dsn, **kwargs):
        connect_calls.append((dsn, kwargs))
        return connection

    connector = PostgresConnector({"AUDITAI_SOURCE_FINANCE_DSN":
        "postgresql://readonly:placeholder@database/finance"}, connect=connect)
    assert connector.discover_tables("finance") == [{"schema": "public", "table": "invoices"}]
    records, truncated = connector.select_rows("finance", "public", "invoices", 2)
    assert records == [{"id": 1, "amount": 120.5}, {"id": 2, "amount": 450.0}]
    assert truncated is True
    assert all(call[1]["options"] == "-c default_transaction_read_only=on" for call in connect_calls)
    assert all(call[1]["connect_timeout"] == 5 for call in connect_calls)
    select_call = next(call for call in connection.calls if isinstance(call[0], Composed))
    assert select_call[1] == (3,)
    assert "Identifier('public')" in repr(select_call[0])
    assert "Identifier('invoices')" in repr(select_call[0])


def test_rejects_unlisted_identifier_before_select():
    connection = FakeConnection()
    connector = PostgresConnector({"AUDITAI_SOURCE_FINANCE_DSN":
        "postgresql://readonly:placeholder@database/finance"}, connect=lambda *a, **k: connection)
    with pytest.raises(ConnectorError, match="not available"):
        connector.select_rows("finance", "public", 'invoices"; DROP TABLE users; --', 10)
    assert not any(isinstance(call[0], Composed) for call in connection.calls)


def test_profiles_and_schema_allowlist_are_environment_only():
    connector = PostgresConnector({"AUDITAI_SOURCE_FINANCE_DSN": "postgresql://host/db",
                                   "AUDITAI_POSTGRES_SCHEMAS": "public,reporting"})
    assert connector.allowed_schemas() == ("public", "reporting")
    assert connector.resolve_dsn("finance") == "postgresql://host/db"
    with pytest.raises(ConnectorError, match="not configured"):
        connector.resolve_dsn("missing")
    with pytest.raises(ConnectorError, match="invalid PostgreSQL connection profile"):
        connector.resolve_dsn("../../secret")


def test_connection_failures_do_not_expose_dsn():
    dsn = "postgresql://readonly:super-secret@database/finance"
    connector = PostgresConnector({"AUDITAI_SOURCE_FINANCE_DSN": dsn},
                                  connect=lambda *a, **k: (_ for _ in ()).throw(RuntimeError(dsn)))
    with pytest.raises(ConnectorError) as captured:
        connector.discover_tables("finance")
    assert "super-secret" not in str(captured.value)
