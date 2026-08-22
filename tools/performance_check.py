"""Deterministic offline load check for the rule engine."""

import argparse
import json
import time
import tracemalloc

from services.rule_engine import evaluate_records


def run_check(*, records=100_000, budget_ms=2000, memory_mb=256) -> dict:
    if not 1 <= records <= 1_000_000:
        raise ValueError("records must be between 1 and 1,000,000")
    population = ({"id": index, "amount": index % 50_000, "vendor": f"vendor-{index % 5000}"} for index in range(records))
    tracemalloc.start()
    started = time.perf_counter()
    result = evaluate_records(population, rule_type="numeric", field="amount", parameters={"operator": ">", "value": 49_000})
    duration_ms = (time.perf_counter() - started) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    metrics = {"records": records, "matches": result.matched_records, "duration_ms": round(duration_ms, 2),
               "records_per_second": round(records / max(duration_ms / 1000, 0.000001)), "peak_memory_mb": round(peak / 1024 / 1024, 2),
               "budget_ms": budget_ms, "memory_budget_mb": memory_mb}
    metrics["passed"] = duration_ms <= budget_ms and metrics["peak_memory_mb"] <= memory_mb
    return metrics


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=int, default=100_000)
    parser.add_argument("--budget-ms", type=int, default=2000)
    parser.add_argument("--memory-mb", type=int, default=256)
    args = parser.parse_args(argv)
    metrics = run_check(records=args.records, budget_ms=args.budget_ms, memory_mb=args.memory_mb)
    print(json.dumps(metrics, sort_keys=True))
    return 0 if metrics["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
