"""Bounded, declarative compound audit-rule evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import operator
from typing import Any, Iterable, Mapping


MAX_DEPTH = 8
MAX_CONDITIONS = 100
MAX_GROUP_ITEMS = 50
MAX_LIST_VALUES = 1_000
MAX_EVIDENCE = 10_000

SCALAR_OPERATORS = {"eq", "ne", "gt", "gte", "lt", "lte"}
TEXT_OPERATORS = {"contains", "not_contains", "starts_with", "ends_with"}
NULL_OPERATORS = {"is_null", "not_null"}
SET_OPERATORS = {"in", "not_in"}
SPECIAL_OPERATORS = {"between", "field_eq", "field_ne", "field_gt", "field_gte", "field_lt", "field_lte",
                     "missing_related_record"}
OPERATORS = SCALAR_OPERATORS | TEXT_OPERATORS | NULL_OPERATORS | SET_OPERATORS | SPECIAL_OPERATORS
THRESHOLD_OPERATORS = {">=", ">", "==", "<=", "<"}


COMPOUND_RULE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object", "additionalProperties": False,
    "required": ["version", "expression"],
    "properties": {
        "version": {"const": 1},
        "alert_when": {"enum": ["condition_met", "condition_not_met"]},
        "expression": {"$ref": "#/$defs/node"},
        "match_threshold": {
            "type": "object", "additionalProperties": False,
            "required": ["operator", "value"],
            "properties": {"operator": {"enum": sorted(THRESHOLD_OPERATORS)},
                           "value": {"type": "number", "minimum": 0},
                           "unit": {"enum": ["count", "percent"]}},
        },
    },
    "$defs": {"node": {"description": "Exactly one of all, any, not, or a leaf condition."}},
}


class CompoundRuleError(ValueError):
    """Invalid or unsafe compound rule definition."""


@dataclass(frozen=True)
class CompoundEvaluationResult:
    scanned_records: int
    condition_matches: int
    selected_records: int
    alarm_triggered: bool
    evidence: tuple[dict[str, Any], ...]
    evidence_truncated: bool
    alert_when: str
    threshold: dict[str, Any]

    def to_dict(self) -> dict:
        return {
            "scanned_records": self.scanned_records, "condition_matches": self.condition_matches,
            "selected_records": self.selected_records, "alarm_triggered": self.alarm_triggered,
            "evidence": list(self.evidence), "evidence_truncated": self.evidence_truncated,
            "alert_when": self.alert_when, "threshold": self.threshold,
        }


def _error(path: str, message: str):
    raise CompoundRuleError(f"{path}: {message}")


def validate_compound_rule(definition: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and normalize the public JSON contract without executing it."""
    if not isinstance(definition, Mapping):
        _error("$", "object required")
    allowed = {"version", "alert_when", "expression", "match_threshold"}
    unknown = set(definition) - allowed
    if unknown:
        _error("$", f"unsupported properties: {sorted(unknown)}")
    if definition.get("version") != 1:
        _error("$.version", "must equal 1")
    alert_when = definition.get("alert_when", "condition_met")
    if alert_when not in {"condition_met", "condition_not_met"}:
        _error("$.alert_when", "must be condition_met or condition_not_met")
    if "expression" not in definition:
        _error("$.expression", "is required")
    counter = [0]
    expression = _validate_node(definition["expression"], "$.expression", 1, counter)
    raw_threshold = definition.get("match_threshold", {"operator": ">=", "value": 1, "unit": "count"})
    if not isinstance(raw_threshold, Mapping):
        _error("$.match_threshold", "object required")
    if set(raw_threshold) - {"operator", "value", "unit"}:
        _error("$.match_threshold", "unsupported properties")
    threshold_operator = raw_threshold.get("operator")
    threshold_value = raw_threshold.get("value")
    unit = raw_threshold.get("unit", "count")
    if threshold_operator not in THRESHOLD_OPERATORS:
        _error("$.match_threshold.operator", "unsupported threshold operator")
    if isinstance(threshold_value, bool) or not isinstance(threshold_value, (int, float)) or threshold_value < 0:
        _error("$.match_threshold.value", "non-negative number required")
    if unit not in {"count", "percent"}:
        _error("$.match_threshold.unit", "must be count or percent")
    if unit == "percent" and threshold_value > 100:
        _error("$.match_threshold.value", "percent cannot exceed 100")
    return {"version": 1, "alert_when": alert_when, "expression": expression,
            "match_threshold": {"operator": threshold_operator, "value": threshold_value, "unit": unit}}


def _validate_node(node: Any, path: str, depth: int, counter: list[int]) -> dict:
    if depth > MAX_DEPTH:
        _error(path, f"maximum depth is {MAX_DEPTH}")
    if not isinstance(node, Mapping):
        _error(path, "object required")
    group_keys = [key for key in ("all", "any", "not") if key in node]
    is_leaf = "operator" in node
    if len(group_keys) + int(is_leaf) != 1:
        _error(path, "exactly one of all, any, not, or operator is required")
    if group_keys:
        key = group_keys[0]
        if set(node) != {key}:
            _error(path, "group nodes cannot contain additional properties")
        if key == "not":
            return {"not": _validate_node(node[key], f"{path}.not", depth + 1, counter)}
        children = node[key]
        if not isinstance(children, list) or not 1 <= len(children) <= MAX_GROUP_ITEMS:
            _error(f"{path}.{key}", f"must contain 1 to {MAX_GROUP_ITEMS} nodes")
        return {key: [_validate_node(child, f"{path}.{key}[{index}]", depth + 1, counter)
                      for index, child in enumerate(children)]}
    counter[0] += 1
    if counter[0] > MAX_CONDITIONS:
        _error(path, f"maximum condition count is {MAX_CONDITIONS}")
    return _validate_condition(node, path)


def _validate_condition(node: Mapping[str, Any], path: str) -> dict:
    allowed = {"operator", "field", "value", "values", "lower", "upper", "other_field", "value_type",
               "case_sensitive", "related_source", "related_field"}
    unknown = set(node) - allowed
    if unknown:
        _error(path, f"unsupported properties: {sorted(unknown)}")
    operation = node.get("operator")
    if operation not in OPERATORS:
        _error(f"{path}.operator", "unsupported operator")
    field = node.get("field")
    if not isinstance(field, str) or not field.strip():
        _error(f"{path}.field", "non-empty string required")
    result = dict(node)
    result["field"] = field.strip()
    if node.get("value_type", "auto") not in {"auto", "number", "text", "date"}:
        _error(f"{path}.value_type", "must be auto, number, text, or date")
    if operation in SCALAR_OPERATORS | TEXT_OPERATORS and "value" not in node:
        _error(f"{path}.value", "is required")
    if operation in SET_OPERATORS:
        values = node.get("values")
        if not isinstance(values, list) or not 1 <= len(values) <= MAX_LIST_VALUES:
            _error(f"{path}.values", f"must contain 1 to {MAX_LIST_VALUES} values")
    if operation == "between" and ("lower" not in node or "upper" not in node):
        _error(path, "between requires lower and upper")
    if operation.startswith("field_") and (not isinstance(node.get("other_field"), str) or not node["other_field"].strip()):
        _error(f"{path}.other_field", "non-empty string required")
    if operation == "missing_related_record":
        if not isinstance(node.get("related_source"), str) or not node["related_source"].strip():
            _error(f"{path}.related_source", "non-empty string required")
        if not isinstance(node.get("related_field"), str) or not node["related_field"].strip():
            _error(f"{path}.related_field", "non-empty string required")
    return result


def _coerce(value: Any, value_type: str):
    if value_type == "number":
        if isinstance(value, bool):
            raise ValueError
        return float(value)
    if value_type == "text":
        return str(value)
    if value_type == "date":
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    return value


def _evaluate_condition(condition, record, related_indexes):
    operation, field = condition["operator"], condition["field"]
    value = record.get(field)
    if operation in NULL_OPERATORS:
        missing = value is None or (isinstance(value, str) and not value.strip())
        return missing if operation == "is_null" else not missing
    if operation == "missing_related_record":
        index_key = (condition["related_source"], condition["related_field"])
        try:
            return value is not None and value not in related_indexes.get(index_key, frozenset())
        except TypeError:
            return False
    if value is None:
        return False
    value_type = condition.get("value_type", "auto")
    if operation in TEXT_OPERATORS:
        left, right = str(value), str(condition["value"])
        if not condition.get("case_sensitive", False):
            left, right = left.casefold(), right.casefold()
        return {"contains": right in left, "not_contains": right not in left,
                "starts_with": left.startswith(right), "ends_with": left.endswith(right)}[operation]
    if operation in SET_OPERATORS:
        candidates = condition["values"]
        found = value in candidates
        return found if operation == "in" else not found
    try:
        left = _coerce(value, value_type)
        if operation == "between":
            return _coerce(condition["lower"], value_type) <= left <= _coerce(condition["upper"], value_type)
        if operation.startswith("field_"):
            right = record.get(condition["other_field"])
            if right is None:
                return False
            right = _coerce(right, value_type)
            operation = operation.removeprefix("field_")
        else:
            right = _coerce(condition["value"], value_type)
        comparator = {"eq": operator.eq, "ne": operator.ne, "gt": operator.gt, "gte": operator.ge,
                      "lt": operator.lt, "lte": operator.le}[operation]
        return comparator(left, right)
    except (TypeError, ValueError, KeyError):
        return False


def _evaluate_node(node, record, related_indexes):
    if "all" in node:
        return all(_evaluate_node(child, record, related_indexes) for child in node["all"])
    if "any" in node:
        return any(_evaluate_node(child, record, related_indexes) for child in node["any"])
    if "not" in node:
        return not _evaluate_node(node["not"], record, related_indexes)
    return _evaluate_condition(node, record, related_indexes)


def _related_indexes(expression, related_sources):
    requested = []
    def visit(node):
        if "operator" in node and node["operator"] == "missing_related_record":
            requested.append((node["related_source"], node["related_field"]))
        for key in ("all", "any"):
            for child in node.get(key, []):
                visit(child)
        if "not" in node:
            visit(node["not"])
    visit(expression)
    indexes = {}
    for source_name, field in requested:
        records = (related_sources or {}).get(source_name)
        if records is None:
            raise CompoundRuleError(f"related source is required: {source_name}")
        values = []
        for record in records:
            if not isinstance(record, Mapping):
                continue
            value = record.get(field)
            if value is not None:
                try:
                    hash(value)
                    values.append(value)
                except TypeError:
                    continue
            if len(values) > 1_000_000:
                raise CompoundRuleError("related source index exceeds 1000000 values")
        indexes[(source_name, field)] = frozenset(values)
    return indexes


def evaluate_compound_rule(records: Iterable[Mapping[str, Any]], definition: Mapping[str, Any], *,
                           related_sources: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
                           max_evidence: int = 1_000) -> CompoundEvaluationResult:
    if isinstance(max_evidence, bool) or not isinstance(max_evidence, int) or not 1 <= max_evidence <= MAX_EVIDENCE:
        raise CompoundRuleError(f"max_evidence must be an integer between 1 and {MAX_EVIDENCE}")
    normalized = validate_compound_rule(definition)
    materialized = []
    for record in records:
        if not isinstance(record, Mapping):
            raise CompoundRuleError("records must contain objects")
        materialized.append(dict(record))
    related_indexes = _related_indexes(normalized["expression"], related_sources)
    condition_results = [_evaluate_node(normalized["expression"], record, related_indexes) for record in materialized]
    condition_matches = sum(condition_results)
    if normalized["alert_when"] == "condition_met":
        selected = [record for record, matched in zip(materialized, condition_results) if matched]
    else:
        selected = [record for record, matched in zip(materialized, condition_results) if not matched]
    threshold = normalized["match_threshold"]
    measured = len(selected) if threshold["unit"] == "count" else (len(selected) / len(materialized) * 100 if materialized else 0)
    alarm_triggered = THRESHOLD_OPERATORS_MAP[threshold["operator"]](measured, threshold["value"])
    return CompoundEvaluationResult(
        scanned_records=len(materialized), condition_matches=condition_matches, selected_records=len(selected),
        alarm_triggered=alarm_triggered, evidence=tuple(selected[:max_evidence]),
        evidence_truncated=len(selected) > max_evidence, alert_when=normalized["alert_when"], threshold=threshold,
    )


THRESHOLD_OPERATORS_MAP = {">=": operator.ge, ">": operator.gt, "==": operator.eq,
                           "<=": operator.le, "<": operator.lt}
