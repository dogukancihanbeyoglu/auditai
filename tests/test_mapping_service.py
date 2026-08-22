from types import SimpleNamespace

import pytest

from services.mapping import MappingApplicationError, apply_mappings


def mapping(mapping_id, source, target, target_type="string", transformation="none", required=False):
    return SimpleNamespace(id=mapping_id, source_column=source, target_field=target,
                           target_type=target_type, transformation=transformation,
                           is_required=required)


def test_applies_safe_transformations_and_preserves_raw_fields():
    result = apply_mappings([{"vendor": "  ATLAS  ", "amount_text": "125.50",
                              "approved": "yes", "posted": "2026-08-22"}], [
        mapping(1, "vendor", "canonical_vendor", transformation="lower"),
        mapping(2, "amount_text", "canonical_amount", "number", "to_number"),
        mapping(3, "approved", "is_approved", "boolean"),
        mapping(4, "posted", "posting_date", "date"),
    ], limit=10)
    assert result.records == [{"vendor": "  ATLAS  ", "amount_text": "125.50",
        "approved": "yes", "posted": "2026-08-22", "canonical_vendor": "atlas",
        "canonical_amount": 125.5, "is_approved": True, "posting_date": "2026-08-22"}]
    assert result.total_errors == 0
    assert result.truncated is False


def test_reports_row_and_field_conversion_errors_with_bounded_values():
    result = apply_mappings([{"amount": "not-a-number", "vendor": ""}], [
        mapping(1, "amount", "canonical_amount", "number", "to_number"),
        mapping(2, "vendor", "canonical_vendor", required=True),
    ], limit=10)
    assert result.records[0]["canonical_amount"] is None
    assert result.records[0]["canonical_vendor"] is None
    assert result.total_errors == 2
    assert [(item.row_index, item.target_field, item.code) for item in result.errors] == [
        (0, "canonical_amount", "conversion"), (0, "canonical_vendor", "required")]


def test_rejects_ambiguous_targets_and_unsafe_limits():
    mappings = [mapping(1, "a", "same"), mapping(2, "b", "same")]
    with pytest.raises(MappingApplicationError, match="only once"):
        apply_mappings([{"a": 1, "b": 2}], mappings, limit=1)
    with pytest.raises(MappingApplicationError, match="between 1 and 10000"):
        apply_mappings([], [], limit=10_001)
