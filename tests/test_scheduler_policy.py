from datetime import datetime, timedelta, timezone

import pytest

from app import create_app
from models import AuditArea, AuditRule, DataSource, RuleExecution, db
from services.scheduler import disable_schedule, inspect_schedule, resume_schedule, run_scheduler_cycle


NOW = datetime(2025, 4, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def app(tmp_path):
    application = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'scheduler.db'}"})
    with application.app_context():
        area = AuditArea(name="Payments")
        source = DataSource(name="Ledger", audit_area=area, config={"records": [{"id": 1, "amount": 200}]})
        rule = AuditRule(name="Large payment", field_name="amount", operator=">", threshold_value=100,
                         severity="high", schedule_interval_minutes=60, next_run_at=NOW,
                         audit_area=area, data_source=source)
        db.session.add_all([area, source, rule])
        db.session.commit()
    return application


def test_disable_resume_and_inspect(app):
    with app.app_context():
        rule = AuditRule.query.one()
        state = disable_schedule(rule)
        assert state["enabled"] is False
        state = resume_schedule(rule, interval_minutes=30, now=NOW, run_immediately=True)
        assert state["enabled"] is True
        assert state["due"] is True
        assert state["interval_minutes"] == 30
        assert inspect_schedule(rule, now=NOW)["locked"] is False


def test_resume_rejects_unsafe_interval(app):
    with app.app_context(), pytest.raises(ValueError, match="between 1 and 10080"):
        resume_schedule(AuditRule.query.one(), interval_minutes=0, now=NOW)


def test_active_lock_prevents_overlapping_execution(app):
    with app.app_context():
        rule = AuditRule.query.one()
        rule.execution_lock_token = "another-worker"
        rule.execution_lock_until = NOW + timedelta(minutes=5)
        db.session.commit()
        cycle = run_scheduler_cycle(now=NOW)
        assert cycle.skipped_locked == 1
        assert RuleExecution.query.count() == 0


def test_running_execution_prevents_overlap_even_without_lock(app):
    with app.app_context():
        rule = AuditRule.query.one()
        db.session.add(RuleExecution(rule=rule, status="running", trigger="manual", started_at=NOW))
        db.session.commit()
        cycle = run_scheduler_cycle(now=NOW)
        assert cycle.skipped_locked == 1
        assert RuleExecution.query.count() == 1


def test_stale_execution_times_out_and_rule_runs(app):
    with app.app_context():
        rule = AuditRule.query.one()
        rule.execution_timeout_seconds = 60
        rule.execution_lock_token = "dead-worker"
        rule.execution_lock_until = NOW + timedelta(minutes=5)
        stale = RuleExecution(rule=rule, status="running", trigger="scheduled", started_at=NOW - timedelta(minutes=2))
        db.session.add(stale)
        db.session.commit()
        cycle = run_scheduler_cycle(now=NOW)
        assert cycle.timed_out == 1
        assert cycle.completed == 1
        assert db.session.get(RuleExecution, stale.id).status == "timed_out"
        assert RuleExecution.query.filter_by(status="completed").count() == 1


def test_failures_retry_with_backoff_then_disable(app):
    with app.app_context():
        rule = AuditRule.query.one()
        rule.rule_type = "unknown"
        rule.schedule_retry_limit = 1
        rule.retry_delay_minutes = 3
        db.session.commit()

        first = run_scheduler_cycle(now=NOW)
        assert first.failed == 1
        assert rule.schedule_enabled is True
        assert rule.next_run_at.replace(tzinfo=timezone.utc) == NOW + timedelta(minutes=3)

        second_now = NOW + timedelta(minutes=3)
        second = run_scheduler_cycle(now=second_now)
        assert second.failed == 1
        assert rule.schedule_enabled is False
        assert [item.attempt for item in RuleExecution.query.order_by(RuleExecution.id)] == [1, 2]
