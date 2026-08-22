# Anomaly detection foundation

AuditAI's detector package performs real, deterministic calculations. It does
not label threshold rules as machine learning and does not simulate unavailable
algorithms.

## Available detectors

- `statistical_zscore`: population z-score per numeric field. Sensitivity maps
  to a documented threshold from 4.0 (least sensitive) to 1.5 (most sensitive).
- `statistical_iqr`: Tukey fences per numeric field. Sensitivity maps to an IQR
  multiplier from 2.5 to 0.5.
- `isolation_forest`: a real scikit-learn Isolation Forest with a fixed random
  seed. It is available only when optional `numpy` and `scikit-learn`
  dependencies are installed. Otherwise it raises `UnsupportedDetector`.

Callers obtain detectors through the registry:

```python
from services.detectors import get_detector

result = get_detector("statistical_iqr").detect(
    records,
    fields=["amount", "days_to_approve"],
    sensitivity=0.7,
    confidence_threshold=0.8,
    max_evidence=100,
)
```

`DetectionResult` distinguishes scanned, analysed and invalid records, reports
the total anomaly count, and retains only the configured evidence sample. Every
evidence item includes the source record index/ID, score, confidence,
per-field contributions and a plain-language explanation.

## Safety and interpretation

- Missing, boolean, non-numeric, NaN and infinite values are excluded and
  counted; they never enter numerical estimators.
- Fewer than five complete records for statistical methods, or ten for
  Isolation Forest, returns `insufficient_data` rather than a fabricated score.
- Constant populations return `no_variance`.
- At most 50 fields and 10,000 evidence items are accepted.
- Statistical confidence is a deterministic score transformation, not a
  calibrated probability of fraud.
- Isolation Forest confidence is the observation's empirical anomaly-score
  rank. Its `contributing_fields` are robust distances from population medians,
  explicitly not native model feature importance.

An anomaly is an unusual observation, not proof of error or fraud. Production
use requires data-quality gates, domain review, feedback capture, monitored
false-positive rates and versioned detector configuration.

## Integration boundary

This package is intentionally independent of Flask and database models. A later
execution integration should dispatch advanced `AuditRule` types through the
registry, persist versioned detection results, and create alerts only after the
configured confidence threshold. Existing deterministic controls must continue
to use `services.rule_engine`.
