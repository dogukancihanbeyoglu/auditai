"""Bounded in-process joins for aliased audit-rule data sources."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from services.mapping import MappingApplicationError, apply_mappings


ALIAS_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
JOIN_TYPES = {"inner", "left"}
JOIN_OPERATORS = {"eq", "casefold_eq", "numeric_eq"}


class FederatedLoadError(ValueError):
    """A safe configuration/population error; no SQL is evaluated."""


@dataclass(frozen=True)
class FederatedLoadResult:
    records: list[dict[str, Any]]
    source_aliases: list[str]
    source_record_counts: dict[str, int]


def load_federated_records(rule, *, max_source_records: int = 10_000,
                           max_output_records: int = 10_000) -> FederatedLoadResult:
    if not 1 <= max_source_records <= 100_000 or not 1 <= max_output_records <= 100_000:
        raise FederatedLoadError("federated record limits are invalid")
    links = list(rule.source_links)
    if not links:
        records = _source_records(rule.data_source, max_source_records)
        return FederatedLoadResult(records=records, source_aliases=[],
                                   source_record_counts={"primary": len(records)})
    links.sort(key=lambda item: (item.priority, item.id or 0))
    _validate_links(rule, links)

    first = links[0]
    base_records = _mapped_source_records(first.data_source, max_source_records)
    aggregate = [_base_record(record, first.alias) for record in base_records]
    counts = {first.alias: len(base_records)}
    aliases = [first.alias]

    for link in links[1:]:
        right_records = _mapped_source_records(link.data_source, max_source_records)
        counts[link.alias] = len(right_records)
        right_fields = _record_fields(link.data_source, right_records)
        index: dict[Any, list[dict[str, Any]]] = {}
        for record in right_records:
            key = _join_key(record.get(link.right_field), link.join_operator)
            if key is not None:
                index.setdefault(key, []).append(record)

        joined = []
        for left in aggregate:
            left_value = left.get(f"{link.join_to_alias}.{link.left_field}")
            matches = index.get(_join_key(left_value, link.join_operator), [])
            if matches:
                for right in matches:
                    joined.append(_merge_record(left, right, link.alias))
                    if len(joined) > max_output_records:
                        raise FederatedLoadError("federated join exceeds the output record limit")
            elif link.join_type == "left":
                joined.append(_merge_record(left, {field: None for field in right_fields}, link.alias))
                if len(joined) > max_output_records:
                    raise FederatedLoadError("federated join exceeds the output record limit")
        aggregate = joined
        aliases.append(link.alias)
    return FederatedLoadResult(records=aggregate, source_aliases=aliases, source_record_counts=counts)


def _validate_links(rule, links) -> None:
    aliases = set()
    if links[0].data_source_id != rule.data_source_id:
        raise FederatedLoadError("the first federated source must be the rule primary data source")
    for index, link in enumerate(links):
        if not ALIAS_PATTERN.fullmatch(link.alias or ""):
            raise FederatedLoadError("source alias must be a safe identifier")
        if link.alias in aliases:
            raise FederatedLoadError("source aliases must be unique")
        if link.data_source.audit_area_id != rule.audit_area_id:
            raise FederatedLoadError("all rule sources must belong to the rule audit area")
        if link.join_type not in JOIN_TYPES or link.join_operator not in JOIN_OPERATORS:
            raise FederatedLoadError("unsupported join type or operator")
        if index == 0:
            if any((link.join_to_alias, link.left_field, link.right_field)):
                raise FederatedLoadError("the primary source cannot contain a join definition")
        else:
            if link.join_to_alias not in aliases:
                raise FederatedLoadError("join_to_alias must reference an earlier source")
            if not link.left_field or not link.right_field:
                raise FederatedLoadError("joined sources require left_field and right_field")
            if link.left_field not in _source_fields_by_alias(links[:index], link.join_to_alias):
                raise FederatedLoadError("left join field does not exist")
            if link.right_field not in _source_fields(link.data_source):
                raise FederatedLoadError("right join field does not exist")
        aliases.add(link.alias)


def _mapped_source_records(source, limit: int) -> list[dict[str, Any]]:
    records = _source_records(source, limit)
    mappings = list(source.field_mappings)
    if not mappings or not records:
        return records
    try:
        result = apply_mappings(records, mappings, limit=len(records))
    except MappingApplicationError as exc:
        raise FederatedLoadError(str(exc)) from exc
    if result.total_errors:
        first = result.errors[0]
        raise FederatedLoadError(
            f"source mapping failed for {first.target_field} at row {first.row_index}")
    return result.records


def _source_records(source, limit: int) -> list[dict[str, Any]]:
    records = list((source.config or {}).get("records", []))
    if len(records) > limit:
        raise FederatedLoadError("source exceeds the federated input record limit")
    if any(not isinstance(record, dict) for record in records):
        raise FederatedLoadError("source records must be objects")
    return [dict(record) for record in records]


def _source_fields(source) -> set[str]:
    fields = {str(column.get("name")) for column in (source.config or {}).get("columns", [])
              if column.get("name")}
    for record in (source.config or {}).get("records", []):
        fields.update(str(key) for key in record)
    fields.update(mapping.target_field for mapping in source.field_mappings)
    return fields


def _source_fields_by_alias(links, alias: str) -> set[str]:
    return _source_fields(next(link.data_source for link in links if link.alias == alias))


def _record_fields(source, records) -> set[str]:
    fields = _source_fields(source)
    for record in records:
        fields.update(record)
    return fields


def _base_record(record: dict[str, Any], alias: str) -> dict[str, Any]:
    return {**record, **{f"{alias}.{key}": value for key, value in record.items()}}


def _merge_record(left: dict[str, Any], right: dict[str, Any], alias: str) -> dict[str, Any]:
    return {**left, **{f"{alias}.{key}": value for key, value in right.items()}}


def _join_key(value: Any, operator: str):
    if value is None:
        return None
    if operator == "eq":
        return f"{type(value).__name__}:{value!r}"
    if operator == "casefold_eq":
        return str(value).strip().casefold()
    if operator == "numeric_eq":
        if isinstance(value, bool):
            return None
        try:
            number = float(value)
            return number if math.isfinite(number) else None
        except (TypeError, ValueError):
            return None
    raise FederatedLoadError("unsupported join operator")
