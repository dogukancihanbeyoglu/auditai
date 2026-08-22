"""Persistence boundary for rule execution, alarms, and evidence."""

from __future__ import annotations

from flask import current_app

from models import Alarm, AuditRule, RuleExecution, db, utcnow
from services.rule_engine import evaluate_records


def run_rule(rule: AuditRule, *, trigger: str = "manual", attempt: int = 1) -> RuleExecution:
    if not rule.is_active:
        raise ValueError("rule is inactive")
    execution = RuleExecution(rule=rule, status="running", trigger=trigger, attempt=attempt, started_at=utcnow())
    db.session.add(execution)
    records = (rule.data_source.config or {}).get("records", [])
    try:
        params = dict(rule.parameters or {})
        if rule.rule_type == "numeric" and "value" not in params:
            params.update(operator=rule.operator, value=rule.threshold_value)
        result = evaluate_records(
            records, rule_type=rule.rule_type, field=rule.field_name, parameters=params,
            max_matches=int(current_app.config.get("EVIDENCE_SAMPLE_LIMIT", 1_000)),
        )
        execution.status = "completed"
        execution.scanned_records = result.scanned_records
        execution.matched_records = result.matched_records
        rule.last_run_at = utcnow()
        if result.matches:
            alarm = Alarm(
                title=rule.name,
                message=(f"{result.matched_records} record(s) matched {rule.rule_type} control; "
                         f"{len(result.matches)} retained as evidence"),
                severity=rule.severity,
                affected_records=result.matches,
                rule=rule, audit_area=rule.audit_area, data_source=rule.data_source,
            )
            rule.trigger_count += 1
            db.session.add(alarm)
        execution.finished_at = utcnow()
        db.session.commit()
        return execution
    except Exception as exc:
        execution.status = "failed"
        execution.error_message = str(exc)[:2000]
        execution.finished_at = utcnow()
        db.session.commit()
        return execution
