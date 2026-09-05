"""Run a deterministic benchmark from generated input artifacts without importing generator code."""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import replace
from json import dumps, loads
from pathlib import Path
from time import perf_counter_ns
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
API_ROOT = PROJECT_ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

_INPUT_SOURCES = ("orders", "payments", "reconciliation_rows", "bank_transactions")
_UNAVAILABLE_TRUTH_REASON = (
    "Ground truth contains scenario labels and entity IDs but no explicit expected candidate "
    "mapping; "
    "truth-derived decision metrics are unavailable."
)


def main() -> None:
    from reconra.audit.events import AuditEvent
    from reconra.metrics.evaluator import EvaluationReport
    from reconra.metrics.throughput import Throughput
    from reconra.policy.reconciliation import ReconciliationPolicy
    from reconra.reconciliation.pipeline import CanonicalDataset, reconcile_deterministic

    args = _parse_args()
    raw_inputs = _load_raw_inputs(_dataset_directory(args.input_root, args.dataset))
    dataset = CanonicalDataset.from_raw_inputs(raw_inputs)
    started_ns = perf_counter_ns()
    policy = ReconciliationPolicy()
    audit_events: list[AuditEvent] = []
    result = reconcile_deterministic(dataset, policy, audit_events=audit_events)
    provider_status = "NOT_APPLICABLE"
    if args.mode == "agent-assisted":
        provider_status = _run_agent_assisted(result, dataset, policy, audit_events)
    elapsed_ns = perf_counter_ns() - started_ns
    record_count = len(dataset.settlement_entries)
    metrics_seed = EvaluationReport.empty(total_records=record_count).with_result(result)
    if args.mode == "agent-assisted":
        metrics_seed = replace(
            metrics_seed,
            agent_assisted=sum(
                event.action == "SYSTEM_AUTO_APPLY" for event in audit_events
            ),
        )
    throughput = Throughput(record_count=record_count, elapsed_ns=elapsed_ns)
    metrics = replace(
        metrics_seed,
        elapsed_ns=elapsed_ns,
        records_per_second=throughput.records_per_second,
    )
    output = args.output or PROJECT_ROOT / "docs" / "evaluation" / f"{args.dataset}-{args.mode}"
    _write_outputs(result, metrics, output, args.dataset, args.mode, provider_status)
    print(
        dumps(
            _benchmark_payload(
                args.dataset, args.mode, output, result, metrics, provider_status
            ),
        )
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a deterministic Reconra benchmark.")
    parser.add_argument(
        "--dataset",
        required=True,
        choices=["clean", "messy-dev", "demo", "heldout", "stress"],
    )
    parser.add_argument("--mode", required=True, choices=["deterministic", "agent-assisted"])
    parser.add_argument(
        "--input-root",
        type=Path,
        default=PROJECT_ROOT / "data" / "generated",
        help="Directory containing one subdirectory per generated dataset role.",
    )
    parser.add_argument("--output", type=Path, help="Directory for the benchmark artifacts.")
    return parser.parse_args()


def _load_raw_inputs(dataset_directory: Path) -> dict[str, object]:
    inputs: dict[str, object] = {}
    for source_name in _INPUT_SOURCES:
        path = dataset_directory / f"{source_name}.json"
        if not path.is_file():
            raise FileNotFoundError(f"required dataset artifact is missing: {path}")
        value: Any = loads(path.read_text(encoding="utf-8"))
        inputs[source_name] = value
    return inputs


def _dataset_directory(input_root: Path, dataset: str) -> Path:
    """Support the generator's selected-role layout and its all-roles subdirectory layout."""
    nested = input_root / dataset
    if all((nested / f"{source_name}.json").is_file() for source_name in _INPUT_SOURCES):
        return nested
    return input_root


def _run_agent_assisted(
    result: Any, dataset: Any, policy: Any, audit_events: list[Any]
) -> str:
    """Execute the production residual path; it remains non-mutating without approval."""
    from app.services.residual_adapter import build_residual_packets

    from agent.orchestrator import reason_residuals
    from agent.providers.gemini import GeminiReasoner

    packets = build_residual_packets(dataset, result, policy)
    reasoner = GeminiReasoner()
    asyncio.run(
        reason_residuals(
            packets,
            reasoner,
            policy,
            available_unexplained_paise=result.unexplained_residual_paise,
            run_id=result.run_id,
            audit_events=audit_events,
        )
    )
    return reasoner.execution_status


def _write_outputs(
    result: Any,
    metrics: Any,
    output: Path,
    dataset: str,
    mode: str,
    provider_status: str,
) -> None:
    from reconra.artifacts.audit import write_audit_log
    from reconra.artifacts.exceptions import write_exception_worklist
    from reconra.artifacts.ledger import write_reconciled_ledger
    from reconra.artifacts.summary import write_reconciliation_summary

    output.mkdir(parents=True, exist_ok=True)
    write_reconciled_ledger(result, output)
    write_exception_worklist(result, output)
    write_audit_log(result, output)
    write_reconciliation_summary(result, metrics, output)
    (output / "benchmark.json").write_text(
        dumps(
            _benchmark_payload(dataset, mode, output, result, metrics, provider_status),
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _benchmark_payload(
    dataset: str,
    mode: str,
    output_directory: Path,
    result: Any,
    metrics: Any,
    provider_status: str = "NOT_APPLICABLE",
) -> dict[str, Any]:
    return {
        "dataset": dataset,
        "mode": mode,
        "agent_provider_status": _agent_provider_status(mode, provider_status),
        "output_directory": str(output_directory),
        "scoring_available": metrics.scoring_available,
        "scoring_unavailable_reason": _UNAVAILABLE_TRUTH_REASON,
        "total_records": metrics.total_records,
        "resolved_records": metrics.resolved_records,
        "deterministic_resolved": metrics.deterministic_resolved,
        "agent_assisted": metrics.agent_assisted,
        "review_required": metrics.review_required,
        "escalated": metrics.escalated,
        "operational_outcome_count": metrics.operational_outcome_count,
        "total_bank_credit_paise": result.total_bank_credit_paise,
        "explained_bank_credit_paise": result.explained_bank_credit_paise,
        "unexplained_residual_paise": result.unexplained_residual_paise,
        "elapsed_ns": metrics.elapsed_ns,
        "records_per_second": {
            "numerator": metrics.records_per_second[0],
            "denominator": metrics.records_per_second[1],
        },
    }


def _agent_provider_status(mode: str, execution_status: str = "NO_RESIDUALS") -> str:
    if mode != "agent-assisted":
        return "NOT_APPLICABLE"
    return execution_status


if __name__ == "__main__":
    main()
