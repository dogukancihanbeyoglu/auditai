import math

import pytest

from services.detectors import detector_capabilities, get_detector
from services.detectors.base import DetectorError, UnsupportedDetector


def test_registry_lists_real_capabilities_and_rejects_unknown():
    capabilities = {item["name"]: item for item in detector_capabilities()}
    assert capabilities["statistical_zscore"]["available"] is True
    assert capabilities["statistical_iqr"]["available"] is True
    assert isinstance(capabilities["isolation_forest"]["available"], bool)
    with pytest.raises(UnsupportedDetector, match="unsupported detector"):
        get_detector("imaginary_ai")


def test_zscore_detects_real_outlier_with_explanation():
    records = [{"id": index, "amount": 10.0} for index in range(20)] + [{"id": "outlier", "amount": 100.0}]
    result = get_detector("statistical_zscore").detect(
        records, fields=["amount"], sensitivity=0.8, confidence_threshold=0.8)
    assert result.status == "completed"
    assert result.anomaly_count == 1
    assert result.evidence[0].record_id == "outlier"
    assert result.evidence[0].contributing_fields["amount"] > result.parameters["z_threshold"]
    assert "standard deviations" in result.evidence[0].explanation


def test_zscore_sensitivity_changes_threshold_deterministically():
    records = [{"value": 0} for _ in range(10)] + [{"value": 30}]
    strict = get_detector("statistical_zscore").detect(records, fields=["value"], sensitivity=0)
    sensitive = get_detector("statistical_zscore").detect(records, fields=["value"], sensitivity=1)
    assert strict.parameters["z_threshold"] == 4.0
    assert strict.anomaly_count == 0
    assert sensitive.parameters["z_threshold"] == 1.5
    assert sensitive.anomaly_count == 1


def test_iqr_handles_multiple_fields_and_bounds_evidence():
    records = [{"id": index, "amount": 10 + index % 5, "days": 1 + index % 3} for index in range(30)]
    records.extend([{"id": "a", "amount": 1000, "days": 2}, {"id": "b", "amount": 900, "days": 100}])
    result = get_detector("statistical_iqr").detect(
        records, fields=["amount", "days"], sensitivity=0.8, confidence_threshold=0.5, max_evidence=1)
    assert result.anomaly_count == 2
    assert len(result.evidence) == 1
    assert result.evidence_truncated is True
    assert set(result.evidence[0].contributing_fields) == {"amount", "days"}


@pytest.mark.parametrize("invalid", [None, "bad", math.nan, math.inf, -math.inf, True])
def test_non_finite_or_non_numeric_rows_are_skipped_safely(invalid):
    records = [{"value": index} for index in range(10)] + [{"value": invalid}]
    result = get_detector("statistical_zscore").detect(records, fields=["value"])
    assert result.scanned_records == 11
    assert result.analyzed_records == 10
    assert result.invalid_records == 1


def test_small_sample_and_constant_columns_are_explicit():
    small = get_detector("statistical_zscore").detect([{"x": 1}] * 4, fields=["x"])
    assert small.status == "insufficient_data"
    assert small.anomaly_count == 0
    constant = get_detector("statistical_iqr").detect([{"x": 1}] * 10, fields=["x"])
    assert constant.status == "no_variance"
    assert constant.anomaly_count == 0


@pytest.mark.parametrize("kwargs,message", [
    ({"fields": []}, "fields are required"),
    ({"fields": ["x"], "sensitivity": 1.1}, "sensitivity"),
    ({"fields": ["x"], "confidence_threshold": -0.1}, "confidence_threshold"),
    ({"fields": ["x"], "max_evidence": 0}, "max_evidence"),
])
def test_configuration_validation(kwargs, message):
    with pytest.raises(DetectorError, match=message):
        get_detector("statistical_zscore").detect([{"x": 1}] * 10, **kwargs)


def test_isolation_forest_is_real_or_explicitly_unsupported():
    detector = get_detector("isolation_forest")
    records = [{"id": index, "x": index % 5, "y": index % 3} for index in range(50)]
    records.append({"id": "outlier", "x": 1000, "y": 1000})
    if not detector.capability()["available"]:
        with pytest.raises(UnsupportedDetector, match="requires the optional"):
            detector.detect(records, fields=["x", "y"])
    else:
        first = detector.detect(records, fields=["x", "y"], sensitivity=0.2, confidence_threshold=0.8)
        second = detector.detect(records, fields=["x", "y"], sensitivity=0.2, confidence_threshold=0.8)
        assert first.to_dict() == second.to_dict()
        assert any(item.record_id == "outlier" for item in first.evidence)
        assert "not feature importance" in next(item for item in first.evidence if item.record_id == "outlier").explanation
