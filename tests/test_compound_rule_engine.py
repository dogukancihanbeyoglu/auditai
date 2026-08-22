from datetime import date

import pytest

from services.compound_rule_engine import (COMPOUND_RULE_SCHEMA, CompoundRuleError,
                                           evaluate_compound_rule, validate_compound_rule)


RECORDS = [
    {"id": 1, "amount": 500, "approved": False, "vendor": "Atlas Office", "vendor_id": "V1", "limit": 100},
    {"id": 2, "amount": 50, "approved": True, "vendor": "Northwind", "vendor_id": "V2", "limit": 100},
    {"id": 3, "amount": 250, "approved": None, "vendor": "Atlas Consulting", "vendor_id": "V3", "limit": 250},
]


def definition(expression, **extra):
    return {"version": 1, "expression": expression, **extra}


def test_nested_and_or_not_evaluation():
    rule = definition({"all": [
        {"field": "amount", "operator": "gte", "value": 200, "value_type": "number"},
        {"any": [
            {"field": "vendor", "operator": "starts_with", "value": "atlas"},
            {"not": {"field": "approved", "operator": "eq", "value": True}},
        ]},
    ]})
    result = evaluate_compound_rule(RECORDS, rule)
    assert result.condition_matches == 2
    assert result.selected_records == 2
    assert [row["id"] for row in result.evidence] == [1, 3]
    assert result.alarm_triggered is True


def test_alert_when_not_met_and_count_threshold():
    rule = definition(
        {"field": "approved", "operator": "eq", "value": True},
        alert_when="condition_not_met",
        match_threshold={"operator": ">=", "value": 2, "unit": "count"},
    )
    result = evaluate_compound_rule(RECORDS, rule)
    assert result.condition_matches == 1
    assert result.selected_records == 2
    assert result.alarm_triggered is True


def test_percent_threshold_and_bounded_evidence():
    rule = definition(
        {"field": "amount", "operator": "gt", "value": 10, "value_type": "number"},
        match_threshold={"operator": ">", "value": 60, "unit": "percent"},
    )
    result = evaluate_compound_rule(RECORDS, rule, max_evidence=1)
    assert result.alarm_triggered is True
    assert result.selected_records == 3
    assert len(result.evidence) == 1
    assert result.evidence_truncated is True


def test_missing_related_record_uses_named_bounded_index():
    rule = definition({"field": "vendor_id", "operator": "missing_related_record",
                       "related_source": "vendors", "related_field": "id"})
    result = evaluate_compound_rule(RECORDS, rule, related_sources={"vendors": [{"id": "V1"}, {"id": "V2"}]})
    assert [row["id"] for row in result.evidence] == [3]
    with pytest.raises(CompoundRuleError, match="related source is required"):
        evaluate_compound_rule(RECORDS, rule)


@pytest.mark.parametrize("expression,expected", [
    ({"field": "amount", "operator": "between", "lower": 100, "upper": 500, "value_type": "number"}, [1, 3]),
    ({"field": "amount", "operator": "field_gt", "other_field": "limit", "value_type": "number"}, [1]),
    ({"field": "vendor", "operator": "in", "values": ["Northwind"]}, [2]),
    ({"field": "approved", "operator": "is_null"}, [3]),
])
def test_multiple_safe_operator_families(expression, expected):
    result = evaluate_compound_rule(RECORDS, definition(expression))
    assert [row["id"] for row in result.evidence] == expected


def test_date_comparison_and_invalid_values_are_non_matches():
    records = [{"id": 1, "posted": "2025-01-01"}, {"id": 2, "posted": "bad"}, {"id": 3, "posted": None}]
    rule = definition({"field": "posted", "operator": "lt", "value": date(2025, 2, 1), "value_type": "date"})
    assert [row["id"] for row in evaluate_compound_rule(records, rule).evidence] == [1]


def test_contract_schema_and_normalized_defaults():
    normalized = validate_compound_rule(definition({"field": "amount", "operator": "gt", "value": 10}))
    assert COMPOUND_RULE_SCHEMA["properties"]["version"] == {"const": 1}
    assert normalized["alert_when"] == "condition_met"
    assert normalized["match_threshold"] == {"operator": ">=", "value": 1, "unit": "count"}


@pytest.mark.parametrize("bad,match", [
    ({}, "version"),
    ({"version": 1, "expression": {"all": [], "extra": True}}, "additional properties"),
    (definition({"field": "x", "operator": "exec", "value": "danger"}), "unsupported operator"),
    (definition({"field": "x", "operator": "in", "values": []}), "must contain"),
    (definition({"field": "x", "operator": "between", "lower": 1}), "requires lower and upper"),
    (definition({"field": "x", "operator": "gt", "value": 1},
                match_threshold={"operator": ">=", "value": 101, "unit": "percent"}), "cannot exceed"),
])
def test_json_contract_rejects_invalid_or_unsafe_shapes(bad, match):
    with pytest.raises(CompoundRuleError, match=match):
        validate_compound_rule(bad)


def test_depth_condition_group_and_evidence_limits():
    node = {"field": "x", "operator": "eq", "value": 1}
    for _ in range(8):
        node = {"not": node}
    with pytest.raises(CompoundRuleError, match="maximum depth"):
        validate_compound_rule(definition(node))
    with pytest.raises(CompoundRuleError, match="1 to 50"):
        validate_compound_rule(definition({"all": [{"field": "x", "operator": "eq", "value": 1}] * 51}))
    leaf = {"field": "x", "operator": "eq", "value": 1}
    nested = {"all": [{"all": [leaf] * 40}, {"all": [leaf] * 40}, {"all": [leaf] * 21}]}
    with pytest.raises(CompoundRuleError, match="maximum condition count"):
        validate_compound_rule(definition(nested))
    with pytest.raises(CompoundRuleError, match="max_evidence"):
        evaluate_compound_rule(RECORDS, definition({"field": "id", "operator": "gt", "value": 0}), max_evidence=0)


def test_non_object_records_are_rejected():
    with pytest.raises(CompoundRuleError, match="records must contain objects"):
        evaluate_compound_rule([{"id": 1}, "bad"], definition({"field": "id", "operator": "gt", "value": 0}))
