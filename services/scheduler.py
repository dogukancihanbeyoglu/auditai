"""Deterministic scheduling service intended for cron or a worker process."""

from datetime import timedelta

from models import AuditRule, db, utcnow
from services.execution import run_rule


def run_due_rules(*, now=None):
    now = now or utcnow()
    due = AuditRule.query.filter(
        AuditRule.is_active.is_(True),
        AuditRule.schedule_interval_minutes.isnot(None),
        AuditRule.schedule_interval_minutes > 0,
        AuditRule.next_run_at <= now,
    ).order_by(AuditRule.next_run_at, AuditRule.id).all()
    executions = []
    for rule in due:
        executions.append(run_rule(rule, trigger="scheduled"))
        # Move from the actual run time to avoid catch-up storms.
        rule.next_run_at = now + timedelta(minutes=rule.schedule_interval_minutes)
        db.session.commit()
    return executions
