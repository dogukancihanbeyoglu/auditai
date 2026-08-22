"""Persistence boundary for rule execution, alarms, and evidence."""

from __future__ import annotations

from flask import current_app

from models import Alarm, AuditRule, RuleExecution, db, utcnow
from services.rule_engine import evaluate_records
from services.detectors import get_detector
from services.mapping import mapped_records_for_rule


def run_rule(rule: AuditRule, *, trigger: str = "manual", attempt: int = 1) -> RuleExecution:
    if not rule.is_active:
        raise ValueError("rule is inactive")
    execution = RuleExecution(rule=rule, status="running", trigger=trigger, attempt=attempt, started_at=utcnow())
    db.session.add(execution)
    try:
        records = mapped_records_for_rule(rule)
        params = dict(rule.parameters or {})
        if rule.rule_type == "numeric" and "value" not in params:
            params.update(operator=rule.operator, value=rule.threshold_value)
        if rule.rule_type == "anomaly":
            detector = get_detector(str(params.get("detector", "statistical_zscore")))
            result = detector.detect(
                records,
                fields=params.get("fields") or [rule.field_name],
                sensitivity=params.get("sensitivity", 0.5),
                confidence_threshold=params.get("confidence_threshold", 0.8),
                max_evidence=min(
                    int(params.get("max_evidence", current_app.config.get("EVIDENCE_SAMPLE_LIMIT", 1_000))),
                    int(current_app.config.get("EVIDENCE_SAMPLE_LIMIT", 1_000)),
                ),
            )
            scanned_records = result.scanned_records
            matched_records = result.anomaly_count
            matches = [item.to_dict() for item in result.evidence]
            result_label = result.detector
        else:
            result = evaluate_records(
                records, rule_type=rule.rule_type, field=rule.field_name, parameters=params,
                max_matches=int(current_app.config.get("EVIDENCE_SAMPLE_LIMIT", 1_000)),
            )
            scanned_records = result.scanned_records
            matched_records = result.matched_records
            matches = result.matches
            result_label = rule.rule_type
        execution.status = "completed"
        execution.scanned_records = scanned_records
        execution.matched_records = matched_records
        rule.last_run_at = utcnow()
        if matches:
            alarm = Alarm(
                title=rule.name,
                message=(f"{matched_records} record(s) matched {result_label} control; "
                         f"{len(matches)} retained as evidence"),
                severity=rule.severity,
                affected_records=matches,
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
