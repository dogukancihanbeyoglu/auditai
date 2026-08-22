from pathlib import Path

import pytest

from config import ConfigurationError, build_runtime_config, normalize_database_url


def test_normalizes_provider_postgres_urls():
    assert normalize_database_url("postgres://user:pass@db/auditai") == (
        "postgresql+psycopg://user:pass@db/auditai"
    )
    assert normalize_database_url("postgresql://user:pass@db/auditai") == (
        "postgresql+psycopg://user:pass@db/auditai"
    )


def test_development_defaults_to_local_sqlite(tmp_path):
    config = build_runtime_config({}, Path(tmp_path / "auditai.db"))
    assert config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:///")
    assert config["AUTO_CREATE_SCHEMA"] is True
    assert config["SESSION_COOKIE_SECURE"] is False


@pytest.mark.parametrize("environment", [
    {"AUDITAI_ENV": "production"},
    {"AUDITAI_ENV": "production", "DATABASE_URL": "sqlite:///unsafe.db",
     "SESSION_SECRET": "x" * 32, "COOKIE_SECURE": "true"},
    {"AUDITAI_ENV": "production", "DATABASE_URL": "postgresql://db/auditai",
     "SESSION_SECRET": "short", "COOKIE_SECURE": "true"},
    {"AUDITAI_ENV": "production", "DATABASE_URL": "postgresql://db/auditai",
     "SESSION_SECRET": "x" * 32, "COOKIE_SECURE": "false"},
])
def test_rejects_unsafe_production_configuration(environment, tmp_path):
    with pytest.raises(ConfigurationError, match="unsafe production configuration"):
        build_runtime_config(environment, Path(tmp_path / "unused.db"))


def test_accepts_complete_production_configuration(tmp_path):
    config = build_runtime_config({"AUDITAI_ENV": "production",
        "DATABASE_URL": "postgresql://auditai:placeholder@database/auditai",
        "SESSION_SECRET": "x" * 32, "COOKIE_SECURE": "true"}, Path(tmp_path / "unused.db"))
    assert config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql+psycopg://")
    assert config["AUTO_CREATE_SCHEMA"] is False
    assert config["SESSION_COOKIE_SECURE"] is True
