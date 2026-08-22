"""API lifecycle for bounded multi-source compound controls."""

from flask import Blueprint, current_app, jsonify, request

from models import AuditArea, AuditRule, DataSource, RuleDataSource, db
from security import record_event, require_role
from services.compound_rule_engine import (COMPOUND_RULE_SCHEMA, CompoundRuleError,
                                           evaluate_compound_rule, validate_compound_rule)
from services.federated_records import FederatedLoadError, load_federated_records


compound_rules_bp = Blueprint("compound_rules", __name__)
SEVERITIES = {"low", "medium", "high", "critical"}


def _serialize_link(link):
    return {
        "id": link.id, "data_source_id": link.data_source_id,
        "data_source_name": link.data_source.name, "alias": link.alias,
        "priority": link.priority, "join_to_alias": link.join_to_alias,
        "left_field": link.left_field, "right_field": link.right_field,
        "join_type": link.join_type, "join_operator": link.join_operator,
    }


def _serialize(rule):
    return {
        "id": rule.id, "name": rule.name, "description": rule.description,
        "severity": rule.severity, "audit_area_id": rule.audit_area_id,
        "is_active": rule.is_active, "trigger_count": rule.trigger_count,
        "definition": rule.parameters, "sources": [_serialize_link(link) for link in rule.source_links],
        "last_run_at": rule.last_run_at.isoformat() if rule.last_run_at else None,
    }


def _build(payload):
    if not isinstance(payload, dict):
        raise ValueError("JSON object required")
    name = str(payload.get("name", "")).strip()
    description = str(payload.get("description", "")).strip()
    severity = str(payload.get("severity", "medium"))
    sources = payload.get("sources")
    if not name or len(name) > 128 or len(description) > 5000:
        raise ValueError("name is required (max 128); description max is 5000")
    if severity not in SEVERITIES:
        raise ValueError("invalid severity")
    if not isinstance(sources, list) or not 1 <= len(sources) <= 12:
        raise ValueError("sources must contain 1 to 12 entries")
    try:
        area_id = int(payload.get("audit_area_id"))
    except (TypeError, ValueError) as exc:
        raise ValueError("valid audit_area_id is required") from exc
    area = db.session.get(AuditArea, area_id)
    if not area:
        raise ValueError("audit area not found")
    definition = validate_compound_rule(payload.get("definition"))
    resolved_sources = []
    seen_sources = set()
    for raw in sources:
        if not isinstance(raw, dict):
            raise ValueError("source entries must be objects")
        try:
            source_id = int(raw.get("data_source_id"))
        except (TypeError, ValueError) as exc:
            raise ValueError("valid source id required") from exc
        source = db.session.get(DataSource, source_id)
        if not source or source.audit_area_id != area.id:
            raise ValueError("all sources must belong to the audit area")
        if source.id in seen_sources:
            raise ValueError("a data source can be linked only once")
        seen_sources.add(source.id)
        resolved_sources.append((raw, source))
    primary = resolved_sources[0][1]
    rule = AuditRule(name=name, description=description, severity=severity, rule_type="compound",
                     field_name="", operator="compound", threshold_value=0, parameters=definition,
                     audit_area=area, data_source=primary)
    for priority, (raw, source) in enumerate(resolved_sources):
        rule.source_links.append(RuleDataSource(
            data_source=source, alias=str(raw.get("alias", "")).strip(), priority=priority,
            join_to_alias=raw.get("join_to_alias"), left_field=raw.get("left_field"),
            right_field=raw.get("right_field"), join_type=raw.get("join_type", "inner"),
            join_operator=raw.get("join_operator", "eq"),
        ))
    return rule


def _evaluate(rule):
    loaded = load_federated_records(
        rule, max_source_records=current_app.config.get("FEDERATED_SOURCE_LIMIT", 10_000),
        max_output_records=current_app.config.get("FEDERATED_OUTPUT_LIMIT", 10_000))
    result = evaluate_compound_rule(
        loaded.records, rule.parameters,
        max_evidence=min(current_app.config.get("EVIDENCE_SAMPLE_LIMIT", 1_000), 10_000))
    return loaded, result


@compound_rules_bp.get("/api/compound-rules/schema")
@require_role()
def compound_schema():
    return jsonify(COMPOUND_RULE_SCHEMA)


@compound_rules_bp.get("/api/compound-rules")
@require_role()
def list_compound_rules():
    rules = AuditRule.query.filter_by(rule_type="compound").order_by(AuditRule.id.desc()).all()
    return jsonify([_serialize(rule) for rule in rules])


@compound_rules_bp.get("/api/compound-rules/<int:rule_id>")
@require_role()
def compound_detail(rule_id):
    return jsonify(_serialize(AuditRule.query.filter_by(id=rule_id, rule_type="compound").first_or_404()))


@compound_rules_bp.post("/api/compound-rules/preview")
@require_role("auditor")
def preview_compound_rule():
    try:
        rule = _build(request.get_json(silent=True))
        loaded, result = _evaluate(rule)
    except (ValueError, CompoundRuleError, FederatedLoadError) as exc:
        return jsonify(error=str(exc)), 400
    return jsonify({**result.to_dict(), "source_aliases": loaded.source_aliases,
                    "source_record_counts": loaded.source_record_counts,
                    "joined_records": len(loaded.records)})


@compound_rules_bp.post("/api/compound-rules")
@require_role("auditor")
def create_compound_rule():
    try:
        rule = _build(request.get_json(silent=True))
        db.session.add(rule)
        db.session.flush()
        loaded, result = _evaluate(rule)
    except (ValueError, CompoundRuleError, FederatedLoadError) as exc:
        db.session.rollback()
        return jsonify(error=str(exc)), 400
    record_event("compound_rule_created", "audit_rule", rule.id,
                 {"source_count": len(rule.source_links), "joined_records": len(loaded.records),
                  "preview_matches": result.selected_records})
    db.session.commit()
    return jsonify(_serialize(rule)), 201
