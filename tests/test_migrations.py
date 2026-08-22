from sqlalchemy import inspect
from flask_migrate import downgrade, upgrade

from app import create_app
from models import db


def test_initial_migration_upgrades_and_downgrades_empty_database(tmp_path):
    database = tmp_path / "migration.db"
    app = create_app({"TESTING": True, "AUTH_REQUIRED": False, "AUTO_CREATE_SCHEMA": False,
                      "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}"})
    with app.app_context():
        upgrade(directory="migrations")
        tables = set(inspect(db.engine).get_table_names())
        assert {"audit_areas", "data_sources", "audit_rules", "rule_executions", "alarms",
                "users", "audit_events", "notifications"}.issubset(tables)

        downgrade(directory="migrations", revision="base")
        assert set(inspect(db.engine).get_table_names()) == {"alembic_version"}
