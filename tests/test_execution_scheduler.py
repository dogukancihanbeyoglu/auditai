from datetime import datetime, timezone

import pytest

from app import create_app
from models import Alarm, AuditArea, AuditRule, DataSource, RuleExecution, db
from services.execution import run_rule
from services.scheduler import run_due_rules


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'service.db'}"})
    with application.app_context():
        area = AuditArea(name="Journal entries")
        source = DataSource(name="Ledger", audit_area=area, config={"records": [
            {"id": 1, "vendor": "Acme"}, {"id": 2, "vendor": "Acme"}, {"id": 3, "vendor": "Other"},
        ]})
        rule = AuditRule(name="Duplicate vendor", field_name="vendor", operator="==", threshold_value=0,
                         rule_type="duplicate", parameters={"fields": ["vendor"]}, severity="high",
                         schedule_interval_minutes=60, next_run_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
                         audit_area=area, data_source=source)
        db.session.add_all([area, source, rule])
        db.session.commit()
    return application


def test_execution_persists_evidence_and_alarm(app):
    with app.app_context():
        execution = run_rule(AuditRule.query.one())
        assert execution.status == "completed"
        assert execution.scanned_records == 3
        assert execution.matched_records == 2
        assert execution.trigger == "manual"
        assert RuleExecution.query.count() == 1
        assert len(Alarm.query.one().affected_records) == 2


def test_scheduler_runs_only_due_rules_and_advances_schedule(app):
    now = datetime(2025, 1, 2, tzinfo=timezone.utc)
    with app.app_context():
        executions = run_due_rules(now=now)
        rule = AuditRule.query.one()
        assert len(executions) == 1
        assert executions[0].trigger == "scheduled"
        # SQLite returns timezone-naive values even for timezone-aware columns.
        assert rule.next_run_at.replace(tzinfo=timezone.utc) == datetime(2025, 1, 2, 1, tzinfo=timezone.utc)
        assert run_due_rules(now=now) == []
