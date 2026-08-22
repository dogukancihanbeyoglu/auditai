"""Concurrency-safe scheduling primitives for cron or worker processes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import or_

from models import AuditRule, RuleExecution, db, utcnow
from services.execution import run_rule


@dataclass(frozen=True)
class SchedulerCycle:
    due: int = 0
    completed: int = 0
    failed: int = 0
    skipped_locked: int = 0
    timed_out: int = 0


def _naive_utc(value: datetime) -> datetime:
    """SQLite persists timestamps without offsets; compare consistently."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def inspect_schedule(rule: AuditRule, *, now=None) -> dict:
    now = _naive_utc(now or utcnow())
    next_run = _naive_utc(rule.next_run_at) if rule.next_run_at else None
    lock_until = _naive_utc(rule.execution_lock_until) if rule.execution_lock_until else None
    return {
        "rule_id": rule.id,
        "enabled": bool(rule.schedule_enabled and rule.schedule_interval_minutes),
        "interval_minutes": rule.schedule_interval_minutes,
        "next_run_at": rule.next_run_at.isoformat() if rule.next_run_at else None,
        "due": bool(rule.schedule_enabled and next_run and next_run <= now),
        "locked": bool(rule.execution_lock_token and lock_until and lock_until > now),
        "lock_until": rule.execution_lock_until.isoformat() if rule.execution_lock_until else None,
        "timeout_seconds": rule.execution_timeout_seconds,
        "retry_limit": rule.schedule_retry_limit,
        "retry_delay_minutes": rule.retry_delay_minutes,
        "consecutive_failures": rule.consecutive_failures,
    }


def disable_schedule(rule: AuditRule) -> dict:
    rule.schedule_enabled = False
    rule.execution_lock_token = None
    rule.execution_lock_until = None
    db.session.commit()
    return inspect_schedule(rule)


def resume_schedule(rule: AuditRule, *, interval_minutes=None, now=None, run_immediately=False) -> dict:
    interval = interval_minutes if interval_minutes is not None else rule.schedule_interval_minutes
    if not isinstance(interval, int) or isinstance(interval, bool) or not 1 <= interval <= 10080:
        raise ValueError("interval_minutes must be an integer between 1 and 10080")
    now = _naive_utc(now or utcnow())
    rule.schedule_interval_minutes = interval
    rule.schedule_enabled = True
    rule.consecutive_failures = 0
    rule.execution_lock_token = None
    rule.execution_lock_until = None
    rule.next_run_at = now if run_immediately else now + timedelta(minutes=interval)
    db.session.commit()
    return inspect_schedule(rule, now=now)


def _expire_stale_executions(rule: AuditRule, now: datetime) -> int:
    cutoff = now - timedelta(seconds=max(1, rule.execution_timeout_seconds))
    stale = RuleExecution.query.filter(
        RuleExecution.rule_id == rule.id,
        RuleExecution.status == "running",
        RuleExecution.started_at <= cutoff,
    ).all()
    for execution in stale:
        execution.status = "timed_out"
        execution.error_message = "execution exceeded configured timeout"
        execution.finished_at = now
    if stale:
        rule.execution_lock_token = None
        rule.execution_lock_until = None
        db.session.commit()
    return len(stale)


def _claim(rule: AuditRule, now: datetime) -> str | None:
    """Atomically claim a rule, preventing overlap across worker processes."""
    token = str(uuid4())
    lock_until = now + timedelta(seconds=max(1, rule.execution_timeout_seconds))
    updated = AuditRule.query.filter(
        AuditRule.id == rule.id,
        AuditRule.schedule_enabled.is_(True),
        or_(AuditRule.execution_lock_until.is_(None), AuditRule.execution_lock_until <= now),
    ).update({AuditRule.execution_lock_token: token, AuditRule.execution_lock_until: lock_until}, synchronize_session=False)
    db.session.commit()
    return token if updated == 1 else None


def _release(rule_id: int, token: str) -> None:
    AuditRule.query.filter(AuditRule.id == rule_id, AuditRule.execution_lock_token == token).update(
        {AuditRule.execution_lock_token: None, AuditRule.execution_lock_until: None}, synchronize_session=False
    )
    db.session.commit()


def run_scheduler_cycle(*, now=None) -> SchedulerCycle:
    now = _naive_utc(now or utcnow())
    due_rules = AuditRule.query.filter(
        AuditRule.is_active.is_(True), AuditRule.schedule_enabled.is_(True),
        AuditRule.schedule_interval_minutes.isnot(None), AuditRule.schedule_interval_minutes > 0,
        AuditRule.next_run_at <= now,
    ).order_by(AuditRule.next_run_at, AuditRule.id).all()
    stats = {"due": len(due_rules), "completed": 0, "failed": 0, "skipped_locked": 0, "timed_out": 0}
    for candidate in due_rules:
        stats["timed_out"] += _expire_stale_executions(candidate, now)
        if RuleExecution.query.filter_by(rule_id=candidate.id, status="running").first():
            stats["skipped_locked"] += 1
            continue
        token = _claim(candidate, now)
        if not token:
            stats["skipped_locked"] += 1
            continue
        rule_id = candidate.id
        try:
            rule = db.session.get(AuditRule, rule_id)
            attempt = rule.consecutive_failures + 1
            execution = run_rule(rule, trigger="scheduled", attempt=attempt)
            if execution.status == "completed":
                stats["completed"] += 1
                rule.consecutive_failures = 0
                rule.next_run_at = now + timedelta(minutes=rule.schedule_interval_minutes)
            else:
                stats["failed"] += 1
                rule.consecutive_failures += 1
                if rule.consecutive_failures > rule.schedule_retry_limit:
                    rule.schedule_enabled = False
                else:
                    backoff = rule.retry_delay_minutes * (2 ** (rule.consecutive_failures - 1))
                    rule.next_run_at = now + timedelta(minutes=backoff)
            db.session.commit()
        finally:
            _release(rule_id, token)
    return SchedulerCycle(**stats)


def run_due_rules(*, now=None):
    """Backward-compatible facade returning executions created in this cycle."""
    before = db.session.query(db.func.max(RuleExecution.id)).scalar() or 0
    run_scheduler_cycle(now=now)
    return RuleExecution.query.filter(RuleExecution.id > before).order_by(RuleExecution.id).all()


def cycle_as_dict(cycle: SchedulerCycle) -> dict:
    return asdict(cycle)
