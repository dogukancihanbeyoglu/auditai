"""Dependency-aware readiness checks; liveness remains intentionally shallow."""

from sqlalchemy import inspect, text

from models import db


REQUIRED_TABLES = {"audit_areas", "data_sources", "audit_rules", "rule_executions", "alarms"}


def readiness_report() -> tuple[dict, int]:
    checks = {}
    try:
        db.session.execute(text("SELECT 1"))
        checks["database"] = {"ready": True}
    except Exception as exc:
        db.session.rollback()
        checks["database"] = {"ready": False, "error": type(exc).__name__}
    try:
        present = set(inspect(db.engine).get_table_names())
        missing = sorted(REQUIRED_TABLES - present)
        checks["schema"] = {"ready": not missing, "missing_tables": missing}
    except Exception as exc:
        checks["schema"] = {"ready": False, "error": type(exc).__name__}
    ready = all(item["ready"] for item in checks.values())
    return {"status": "ready" if ready else "not_ready", "checks": checks}, 200 if ready else 503
