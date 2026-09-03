"""Export deterministic controller artifacts from canonical input JSON files."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path
from time import perf_counter_ns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def main() -> None:
    from reconra.metrics.evaluator import EvaluationReport
    from reconra.metrics.throughput import Throughput
    from reconra.policy.reconciliation import ReconciliationPolicy
    from reconra.reconciliation.pipeline import CanonicalDataset, reconcile_deterministic
    from run_benchmark import _load_raw_inputs, _write_outputs

    parser = argparse.ArgumentParser(description="Export Reconra controller artifacts.")
    parser.add_argument("--input-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dataset = CanonicalDataset.from_raw_inputs(_load_raw_inputs(args.input_directory))
    started_ns = perf_counter_ns()
    result = reconcile_deterministic(dataset, ReconciliationPolicy())
    elapsed_ns = perf_counter_ns() - started_ns
    record_count = len(dataset.settlement_entries)
    metrics_seed = EvaluationReport.empty(total_records=record_count).with_result(result)
    throughput = Throughput(record_count, elapsed_ns)
    metrics = replace(
        metrics_seed,
        elapsed_ns=elapsed_ns,
        records_per_second=throughput.records_per_second,
    )
    _write_outputs(result, metrics, args.output, "import", "deterministic")
    print(args.output)


if __name__ == "__main__":
    main()
