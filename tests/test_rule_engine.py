from datetime import date

import pytest

from services.rule_engine import InvalidRule, evaluate_records


RECORDS = [
    {"id": 1, "amount": "125.50", "vendor": "Atlas Office", "posted": "2025-01-10", "approved": None, "limit": 100},
    {"id": 2, "amount": 40, "vendor": "Northwind", "posted": "2025-03-01", "approved": "yes", "limit": 50},
    {"id": 3, "amount": 125.50, "vendor": "atlas office", "posted": "bad-date", "approved": "", "limit": 125.50},
]


def ids(result):
    return [record["id"] for record in result.matches]


def test_numeric_and_invalid_source_values():
    records = RECORDS + [{"id": 4, "amount": "not-a-number"}]
    result = evaluate_records(records, rule_type="numeric", field="amount", parameters={"operator": ">", "value": 100})
    assert result.scanned_records == 4
    assert ids(result) == [1, 3]


def test_text_case_insensitive_contains():
    result = evaluate_records(RECORDS, rule_type="text", field="vendor", parameters={"operator": "contains", "value": "ATLAS"})
    assert ids(result) == [1, 3]


def test_date_age_and_bad_source_date():
    result = evaluate_records(RECORDS, rule_type="date", field="posted", parameters={"operator": "older_than_days", "days": 30}, today=date(2025, 3, 15))
    assert ids(result) == [1]


def test_null_and_blank_values():
    result = evaluate_records(RECORDS, rule_type="null", field="approved", parameters={"operator": "is_null"})
    assert ids(result) == [1, 3]


def test_duplicate_composite_key():
    result = evaluate_records(RECORDS, rule_type="duplicate", parameters={"fields": ["amount"], "normalize_numeric": True})
    assert ids(result) == [1, 3]


def test_field_comparison():
    result = evaluate_records(RECORDS, rule_type="comparison", field="amount", parameters={"operator": ">", "right_field": "limit"})
    assert ids(result) == [1]


def test_invalid_rule_is_rejected_instead_of_executed():
    with pytest.raises(InvalidRule, match="unsupported text operator"):
        evaluate_records(RECORDS, rule_type="text", field="vendor", parameters={"operator": "regex", "value": ".*"})


def test_evidence_sampling_retains_total_match_count():
    records = [{"id": index, "amount": 100} for index in range(20)]
    result = evaluate_records(records, rule_type="numeric", field="amount",
                              parameters={"operator": ">", "value": 10}, max_matches=3)
    assert result.scanned_records == 20
    assert result.matched_records == 20
    assert len(result.matches) == 3
