"""Common immutable result types and validation helpers for detectors."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Iterable, Mapping


class DetectorError(ValueError):
    """Invalid detector configuration or input."""


class UnsupportedDetector(DetectorError):
    """A requested detector is not installed or implemented."""


@dataclass(frozen=True)
class DetectionEvidence:
    record_index: int
    record_id: Any
    score: float
    confidence: float
    contributing_fields: dict[str, float]
    explanation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DetectionResult:
    detector: str
    status: str
    scanned_records: int
    analyzed_records: int
    invalid_records: int
    anomaly_count: int
    evidence: tuple[DetectionEvidence, ...]
    parameters: dict[str, Any]
    message: str

    @property
    def evidence_truncated(self) -> bool:
        return self.anomaly_count > len(self.evidence)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["evidence"] = [item.to_dict() for item in self.evidence]
        payload["evidence_truncated"] = self.evidence_truncated
        return payload


def validate_options(fields: Iterable[str], sensitivity: float, confidence_threshold: float,
                     max_evidence: int) -> tuple[tuple[str, ...], float, float, int]:
    normalized = tuple(dict.fromkeys(str(field).strip() for field in fields if str(field).strip()))
    if not normalized or len(normalized) > 50:
        raise DetectorError("between 1 and 50 fields are required")
    if isinstance(sensitivity, bool) or not 0 <= float(sensitivity) <= 1:
        raise DetectorError("sensitivity must be between 0 and 1")
    if isinstance(confidence_threshold, bool) or not 0 <= float(confidence_threshold) <= 1:
        raise DetectorError("confidence_threshold must be between 0 and 1")
    if isinstance(max_evidence, bool) or not isinstance(max_evidence, int) or not 1 <= max_evidence <= 10_000:
        raise DetectorError("max_evidence must be an integer between 1 and 10000")
    return normalized, float(sensitivity), float(confidence_threshold), max_evidence


def finite_matrix(records: Iterable[Mapping[str, Any]], fields: tuple[str, ...]):
    materialized = [dict(record) for record in records]
    valid = []
    invalid = 0
    for index, record in enumerate(materialized):
        values = []
        try:
            for field in fields:
                value = record.get(field)
                if isinstance(value, bool):
                    raise ValueError
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError
                values.append(number)
        except (TypeError, ValueError):
            invalid += 1
            continue
        valid.append((index, record.get("id", index), tuple(values)))
    return materialized, valid, invalid


def bounded_evidence(items: list[DetectionEvidence], max_evidence: int) -> tuple[DetectionEvidence, ...]:
    # Highest score first, stable record order for deterministic ties.
    return tuple(sorted(items, key=lambda item: (-item.score, item.record_index))[:max_evidence])
