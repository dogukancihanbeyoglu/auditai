"""Authenticated API for read-only PostgreSQL source profiles."""

from flask import Blueprint, current_app, jsonify, request

from models import AuditArea, DataSource, db, utcnow
from postgres_connector import ConnectorError, PostgresConnector
from security import require_role


postgres_bp = Blueprint("postgres_sources", __name__)


def _connector() -> PostgresConnector:
    factory = current_app.config.get("POSTGRES_CONNECTOR_FACTORY", PostgresConnector)
    return factory()


@postgres_bp.get("/api/connectors/postgresql/<profile>/tables")
@require_role()
def discover_postgres_tables(profile):
    try:
        return jsonify(profile=profile, tables=_connector().discover_tables(profile))
    except ConnectorError as exc:
        return jsonify(error=str(exc)), 400


@postgres_bp.get("/api/connectors/postgresql/<profile>/columns")
@require_role()
def discover_postgres_columns(profile):
    schema_name = request.args.get("schema", "")
    table_name = request.args.get("table", "")
    if not schema_name or not table_name:
        return jsonify(error="schema and table are required"), 400
    try:
        return jsonify(profile=profile, schema=schema_name, table=table_name,
                       columns=_connector().discover_columns(profile, schema_name, table_name))
    except ConnectorError as exc:
        return jsonify(error=str(exc)), 400


@postgres_bp.post("/api/data-sources/postgresql")
@require_role("auditor")
def import_postgres_source():
    payload = request.get_json(silent=True) or {}
    required = ("profile", "schema", "table", "audit_area_id")
    if any(payload.get(item) in (None, "") for item in required):
        return jsonify(error="profile, schema, table and audit_area_id are required"), 400
    try:
        area = db.session.get(AuditArea, int(payload["audit_area_id"]))
        if not area:
            return jsonify(error="audit area not found"), 400
        limit = min(max(int(payload.get("limit", 1_000)), 1), 10_000)
        connector = _connector()
        records, truncated = connector.select_rows(payload["profile"], payload["schema"],
                                                    payload["table"], limit)
        columns = connector.discover_columns(payload["profile"], payload["schema"], payload["table"])
        # Deliberately persist only the environment profile name and source coordinates, never its DSN.
        config = {"profile": payload["profile"], "schema": payload["schema"],
                  "table": payload["table"], "columns": columns, "records": records,
                  "truncated": truncated, "import_limit": limit}
        source = DataSource(name=str(payload.get("name") or payload["table"])[:128],
                            source_type="postgresql", config=config, audit_area=area, last_sync=utcnow())
        db.session.add(source)
        db.session.commit()
        return jsonify(source_id=source.id, name=source.name, record_count=len(records),
                       columns=columns, truncated=truncated), 201
    except (ConnectorError, TypeError, ValueError) as exc:
        return jsonify(error=str(exc)), 400
