"""Safe anomaly detector registry."""

from services.detectors.base import DetectionEvidence, DetectionResult, DetectorError, UnsupportedDetector
from services.detectors.isolation_forest import IsolationForestDetector
from services.detectors.statistical import IQRDetector, ZScoreDetector


DETECTORS = {
    "statistical_zscore": ZScoreDetector(),
    "statistical_iqr": IQRDetector(),
    "isolation_forest": IsolationForestDetector(),
}


def get_detector(name: str):
    try:
        return DETECTORS[name]
    except KeyError as exc:
        raise UnsupportedDetector(f"unsupported detector: {name}") from exc


def detector_capabilities() -> list[dict]:
    return [detector.capability() for detector in DETECTORS.values()]


__all__ = ["DetectionEvidence", "DetectionResult", "DetectorError", "UnsupportedDetector",
           "get_detector", "detector_capabilities"]
