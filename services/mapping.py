"""Deterministic, code-free field mapping and type conversion."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Sequence

from models import FieldMapping


class MappingApplicationError(ValueError):
    """Raised for an invalid mapping definition or required mapped-field failure."""


@dataclass(frozen=True)
class MappingError:
    row_index: int
    mapping_id: int
    source_column: str
    target_field: str
    code: str
    message: str
    value: Any

    def to_dict(self) -> dict[str, Any]:
        return {"row_index": self.row_index, "mapping_id": self.mapping_id,
                "source_column": self.source_column, "target_field": self.target_field,
                "code": self.code, "message": self.message, "value": _safe_value(self.value)}


@dataclass(frozen=True)
class MappingResult:
    records: list[dict[str, Any]]
    errors: list[MappingError]
    total_errors: int
    input_record_count: int
    truncated: bool


def apply_mappings(records: Iterable[dict[str, Any]], mappings: Sequence[FieldMapping], *,
                   limit: int, max_errors: int = 100) -> MappingResult:
    if not 1 <= limit <= 10_000:
        raise MappingApplicationError("mapping limit must be between 1 and 10000")
    if not 1 <= max_errors <= 1_000:
        raise MappingApplicationError("max_errors must be between 1 and 1000")
    ordered = sorted(mappings, key=lambda item: item.id or 0)
    targets = [item.target_field for item in ordered]
    if len(targets) != len(set(targets)):
        raise MappingApplicationError("each target_field may be mapped only once per source")

    materialized = list(records)
    output = []
    errors: list[MappingError] = []
    total_errors = 0
    for row_index, raw_record in enumerate(materialized[:limit]):
        if not isinstance(raw_record, dict):
            raise MappingApplicationError("source records must be objects")
        mapped = dict(raw_record)
        for mapping in ordered:
            raw_value = raw_record.get(mapping.source_column)
            try:
                if mapping.is_required and _empty(raw_value):
                    raise ValueError("required source value is empty")
                mapped[mapping.target_field] = _convert(raw_value, mapping.transformation,
                                                        mapping.target_type)
            except (TypeError, ValueError, OverflowError) as exc:
                mapped[mapping.target_field] = None
                total_errors += 1
                if len(errors) < max_errors:
                    errors.append(MappingError(row_index=row_index, mapping_id=mapping.id,
                        source_column=mapping.source_column, target_field=mapping.target_field,
                        code="required" if mapping.is_required and _empty(raw_value) else "conversion",
                        message=str(exc), value=raw_value))
        output.append(mapped)
    return MappingResult(records=output, errors=errors, total_errors=total_errors,
                         input_record_count=len(materialized),
                         truncated=len(materialized) > limit)


def mapped_records_for_rule(rule, *, max_records: int = 10_000) -> list[dict[str, Any]]:
    records = list((rule.data_source.config or {}).get("records", []))
    if len(records) > max_records:
        raise MappingApplicationError("source exceeds the mapped rule execution limit")
    mappings = list(rule.data_source.field_mappings)
    if not mappings:
        return records
    result = (apply_mappings(records, mappings, limit=max(1, len(records))) if records
              else MappingResult([], [], 0, 0, False))
    required_targets = _rule_fields(rule)
    relevant_errors = [error for error in result.errors if error.target_field in required_targets]
    if relevant_errors:
        first = relevant_errors[0]
        raise MappingApplicationError(
            f"mapping failed for rule field {first.target_field} at row {first.row_index}")
    return result.records


def _rule_fields(rule) -> set[str]:
    params = dict(rule.parameters or {})
    fields = {rule.field_name} if rule.field_name else set()
    if rule.rule_type in {"duplicate", "anomaly"}:
        fields.update(str(item) for item in params.get("fields", []) if item)
    if rule.rule_type == "comparison" and params.get("right_field"):
        fields.add(str(params["right_field"]))
    return fields


def _convert(value: Any, transformation: str, target_type: str) -> Any:
    if value is None:
        return None
    transformed = value
    if transformation in {"trim", "lower", "upper"}:
        transformed = str(value).strip()
        if transformation == "lower":
            transformed = transformed.lower()
        elif transformation == "upper":
            transformed = transformed.upper()
    elif transformation == "to_integer":
        transformed = _integer(value)
    elif transformation == "to_number":
        transformed = _number(value)
    elif transformation != "none":
        raise ValueError("unsupported transformation")

    converters = {"string": lambda item: str(item), "integer": _integer,
                  "number": _number, "boolean": _boolean, "date": _date,
                  "datetime": _datetime}
    try:
        return converters[target_type](transformed)
    except KeyError as exc:
        raise ValueError("unsupported target type") from exc


def _integer(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("boolean cannot be converted to integer")
    number = float(str(value).strip())
    if not math.isfinite(number) or not number.is_integer():
        raise ValueError("value is not an integer")
    return int(number)


def _number(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("boolean cannot be converted to number")
    number = float(str(value).strip())
    if not math.isfinite(number):
        raise ValueError("number must be finite")
    return number


def _boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().casefold()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError("value is not a supported boolean")


def _date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(str(value).strip()).isoformat()


def _datetime(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00")).isoformat()


def _empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    text = str(value)
    return text if len(text) <= 200 else text[:197] + "..."
