"""Environment-derived runtime configuration with production guardrails."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path


class ConfigurationError(RuntimeError):
    """Raised when deployment settings are incomplete or unsafe."""


def _truthy(value: str | None) -> bool:
    return (value or "").lower() in {"1", "true", "yes", "on"}


def normalize_database_url(url: str) -> str:
    """Use SQLAlchemy's psycopg 3 dialect and accept common provider URLs."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def build_runtime_config(environ: Mapping[str, str], default_db: Path) -> dict:
    environment = environ.get("AUDITAI_ENV", "development").strip().lower()
    production = environment == "production"
    database_url = environ.get("DATABASE_URL", "").strip()
    session_secret = environ.get("SESSION_SECRET", "")

    if production:
        errors = []
        if not database_url:
            errors.append("DATABASE_URL is required")
        elif not database_url.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
            errors.append("DATABASE_URL must use PostgreSQL")
        if len(session_secret) < 32:
            errors.append("SESSION_SECRET must contain at least 32 characters")
        if not _truthy(environ.get("COOKIE_SECURE")):
            errors.append("COOKIE_SECURE must be true")
        if errors:
            raise ConfigurationError("unsafe production configuration: " + "; ".join(errors))

    return {
        "AUDITAI_ENV": environment,
        "SQLALCHEMY_DATABASE_URI": normalize_database_url(database_url) if database_url
        else f"sqlite:///{default_db}",
        "SECRET_KEY": session_secret or None,
        "SESSION_COOKIE_SECURE": _truthy(environ.get("COOKIE_SECURE")),
        "AUTO_CREATE_SCHEMA": not production and not (
            environ.get("AUTO_CREATE_SCHEMA", "true").lower() in {"0", "false", "no", "off"}
        ),
    }
