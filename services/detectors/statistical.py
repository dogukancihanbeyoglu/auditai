"""Explainable univariate z-score and IQR detectors."""

from __future__ import annotations

from math import erf, exp, sqrt
from statistics import mean, median, pstdev, quantiles

from services.detectors.base import (DetectionEvidence, DetectionResult, bounded_evidence,
                                     finite_matrix, validate_options)


MIN_SAMPLES = 5


def _empty(name, scanned, analyzed, invalid, parameters, status, message):
    return DetectionResult(name, status, scanned, analyzed, invalid, 0, (), parameters, message)


class ZScoreDetector:
    name = "statistical_zscore"

    def capability(self):
        return {"name": self.name, "available": True, "minimum_samples": MIN_SAMPLES,
                "description": "Population z-score with per-field explanations"}

    def detect(self, records, *, fields, sensitivity=0.5, confidence_threshold=0.8, max_evidence=100):
        fields, sensitivity, confidence_threshold, max_evidence = validate_options(
            fields, sensitivity, confidence_threshold, max_evidence)
        materialized, valid, invalid = finite_matrix(records, fields)
        threshold = round(4.0 - (2.5 * sensitivity), 6)
        parameters = {"fields": list(fields), "sensitivity": sensitivity,
                      "confidence_threshold": confidence_threshold, "z_threshold": threshold}
        if len(valid) < MIN_SAMPLES:
            return _empty(self.name, len(materialized), len(valid), invalid, parameters,
                          "insufficient_data", f"at least {MIN_SAMPLES} complete finite records are required")
        columns = list(zip(*(values for _, _, values in valid)))
        centers = [mean(column) for column in columns]
        deviations = [pstdev(column) for column in columns]
        active = [index for index, deviation in enumerate(deviations) if deviation > 0]
        if not active:
            return _empty(self.name, len(materialized), len(valid), invalid, parameters,
                          "no_variance", "all selected fields are constant")
        detections = []
        for record_index, record_id, values in valid:
            contributions = {fields[i]: round(abs(values[i] - centers[i]) / deviations[i], 6) for i in active}
            score = max(contributions.values())
            confidence = erf(score / sqrt(2))
            if score >= threshold and confidence >= confidence_threshold:
                strongest = max(contributions, key=contributions.get)
                detections.append(DetectionEvidence(
                    record_index, record_id, round(score, 6), round(confidence, 6), contributions,
                    f"{strongest} is {contributions[strongest]:.3f} standard deviations from its mean "
                    f"(threshold {threshold:.3f}).",
                ))
        return DetectionResult(self.name, "completed", len(materialized), len(valid), invalid, len(detections),
                               bounded_evidence(detections, max_evidence), parameters,
                               "z-score evaluation completed")


class IQRDetector:
    name = "statistical_iqr"

    def capability(self):
        return {"name": self.name, "available": True, "minimum_samples": MIN_SAMPLES,
                "description": "Tukey IQR fences with per-field explanations"}

    def detect(self, records, *, fields, sensitivity=0.5, confidence_threshold=0.8, max_evidence=100):
        fields, sensitivity, confidence_threshold, max_evidence = validate_options(
            fields, sensitivity, confidence_threshold, max_evidence)
        materialized, valid, invalid = finite_matrix(records, fields)
        multiplier = round(2.5 - (2.0 * sensitivity), 6)
        parameters = {"fields": list(fields), "sensitivity": sensitivity,
                      "confidence_threshold": confidence_threshold, "iqr_multiplier": multiplier}
        if len(valid) < MIN_SAMPLES:
            return _empty(self.name, len(materialized), len(valid), invalid, parameters,
                          "insufficient_data", f"at least {MIN_SAMPLES} complete finite records are required")
        columns = list(zip(*(values for _, _, values in valid)))
        bounds = []
        for column in columns:
            q1, _, q3 = quantiles(column, n=4, method="inclusive")
            spread = q3 - q1
            bounds.append((q1 - multiplier * spread, q3 + multiplier * spread, spread))
        active = [index for index, (_, _, spread) in enumerate(bounds) if spread > 0]
        if not active:
            return _empty(self.name, len(materialized), len(valid), invalid, parameters,
                          "no_variance", "all selected fields have zero interquartile range")
        detections = []
        for record_index, record_id, values in valid:
            contributions = {}
            for i in active:
                lower, upper, spread = bounds[i]
                distance = max(lower - values[i], values[i] - upper, 0) / spread
                contributions[fields[i]] = round(distance, 6)
            score = max(contributions.values())
            confidence = 0.0 if score <= 0 else 0.5 + 0.5 * (1 - exp(-score))
            if score > 0 and confidence >= confidence_threshold:
                strongest = max(contributions, key=contributions.get)
                detections.append(DetectionEvidence(
                    record_index, record_id, round(score, 6), round(confidence, 6), contributions,
                    f"{strongest} is {contributions[strongest]:.3f} IQR widths beyond its Tukey fence "
                    f"(multiplier {multiplier:.3f}).",
                ))
        return DetectionResult(self.name, "completed", len(materialized), len(valid), invalid, len(detections),
                               bounded_evidence(detections, max_evidence), parameters,
                               "IQR evaluation completed")
