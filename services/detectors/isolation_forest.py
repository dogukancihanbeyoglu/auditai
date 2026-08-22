"""Optional real Isolation Forest detector; never simulates unavailable ML."""

from __future__ import annotations

from services.detectors.base import (DetectionEvidence, DetectionResult, UnsupportedDetector,
                                     bounded_evidence, finite_matrix, validate_options)

try:
    import numpy as np
    from sklearn.ensemble import IsolationForest
except ImportError:  # Optional dependency is intentionally explicit.
    np = None
    IsolationForest = None


class IsolationForestDetector:
    name = "isolation_forest"

    def capability(self):
        return {"name": self.name, "available": IsolationForest is not None,
                "minimum_samples": 10, "description": "scikit-learn Isolation Forest"}

    def detect(self, records, *, fields, sensitivity=0.5, confidence_threshold=0.8, max_evidence=100):
        if IsolationForest is None:
            raise UnsupportedDetector(
                "isolation_forest requires the optional scikit-learn and numpy dependencies")
        fields, sensitivity, confidence_threshold, max_evidence = validate_options(
            fields, sensitivity, confidence_threshold, max_evidence)
        materialized, valid, invalid = finite_matrix(records, fields)
        contamination = round(0.01 + sensitivity * 0.19, 6)
        parameters = {"fields": list(fields), "sensitivity": sensitivity,
                      "confidence_threshold": confidence_threshold, "contamination": contamination,
                      "random_state": 42}
        if len(valid) < 10:
            return DetectionResult(self.name, "insufficient_data", len(materialized), len(valid), invalid, 0, (),
                                   parameters, "at least 10 complete finite records are required")
        matrix = np.asarray([values for _, _, values in valid], dtype=float)
        if np.all(np.ptp(matrix, axis=0) == 0):
            return DetectionResult(self.name, "no_variance", len(materialized), len(valid), invalid, 0, (),
                                   parameters, "all selected fields are constant")
        model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100, n_jobs=1)
        labels = model.fit_predict(matrix)
        raw_scores = -model.score_samples(matrix)
        order = np.argsort(np.argsort(raw_scores, kind="stable"), kind="stable")
        confidences = (order + 1) / len(raw_scores)
        medians = np.median(matrix, axis=0)
        scales = np.median(np.abs(matrix - medians), axis=0)
        scales[scales == 0] = 1.0
        detections = []
        for row, (record_index, record_id, values) in enumerate(valid):
            confidence = float(confidences[row])
            if labels[row] != -1 or confidence < confidence_threshold:
                continue
            contributions = {field: round(float(abs(values[i] - medians[i]) / scales[i]), 6)
                             for i, field in enumerate(fields)}
            strongest = max(contributions, key=contributions.get)
            detections.append(DetectionEvidence(
                record_index, record_id, round(float(raw_scores[row]), 6), round(confidence, 6), contributions,
                f"Isolation Forest classified the record as anomalous; {strongest} has the largest "
                "robust distance from the population median. Contributions explain the input distance, "
                "not feature importance from the model.",
            ))
        return DetectionResult(self.name, "completed", len(materialized), len(valid), invalid, len(detections),
                               bounded_evidence(detections, max_evidence), parameters,
                               "Isolation Forest evaluation completed")
