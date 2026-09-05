"""Production reconciliation orchestration over sanitized input artifacts."""

import asyncio
from datetime import UTC, datetime
from json import loads
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from uuid import uuid4

from app.services.residual_adapter import build_residual_packets
from app.services.run_store import RunStore
from reconra.artifacts.audit import write_audit_log
from reconra.artifacts.exceptions import write_exception_worklist
from reconra.artifacts.ledger import write_reconciled_ledger
from reconra.artifacts.summary import write_reconciliation_summary
from reconra.audit.events import AuditEvent, decision_audit_event
from reconra.metrics.evaluator import EvaluationReport
from reconra.models.exception import ReconciliationException, ResolutionStatus
from reconra.models.result import DeterministicMatch, ReconciliationResult
from reconra.policy.reconciliation import ReconciliationPolicy
from reconra.reconciliation.pipeline import CanonicalDataset, reconcile_deterministic
from reconra.reconciliation.state import ReconciliationState

from agent import orchestrator
from agent.orchestrator import ResidualApprovalContext
from agent.providers.gemini import GeminiReasoner

_INPUT_SOURCES = ("orders", "payments", "reconciliation_rows", "bank_transactions")
_ARTIFACT_NAMES = (
    "audit_log.json",
    "exception_worklist.csv",
    "reconciled_ledger.csv",
    "reconciliation_summary.json",
)
_ARTIFACT_CONTENT_TYPES = {
    "audit_log.json": "application/json",
    "exception_worklist.csv": "text/csv",
    "reconciled_ledger.csv": "text/csv",
    "reconciliation_summary.json": "application/json",
}
run_store = RunStore()


class RunActionError(Exception):
    """Typed safe failure for an action against short-lived run state."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def reconcile_demo() -> dict[str, object]:
    """Load only the tracked curated input fixture and run the normal engine path."""
    input_directory = Path(__file__).resolve().parents[4] / "data" / "demo" / "input"
    raw_inputs = {
        source: loads((input_directory / f"{source}.json").read_text(encoding="utf-8"))
        for source in _INPUT_SOURCES
    }
    return reconcile_inputs(raw_inputs)


def reconcile_inputs(raw_inputs: dict[str, object]) -> dict[str, object]:
    """Run canonical input and retain only the active run in volatile memory."""
    dataset = CanonicalDataset.from_raw_inputs(raw_inputs)
    run_id = f"run_{uuid4().hex[:20]}"
    audit_events: list[AuditEvent] = []
    policy = ReconciliationPolicy()
    result = reconcile_deterministic(dataset, policy, run_id=run_id, audit_events=audit_events)
    packets = build_residual_packets(dataset, result, policy)
    contexts = asyncio.run(
        orchestrator.reason_residuals(
            packets,
            GeminiReasoner(),
            policy,
            available_unexplained_paise=result.unexplained_residual_paise,
            run_id=run_id,
            audit_events=audit_events,
        )
    )
    review_contexts = _store_review_contexts(result, contexts)
    stored: dict[str, Any] = {
        "result": result,
        "state": _state_from_result(result),
        "policy": policy,
        "packets": packets,
        "review_contexts": review_contexts,
        "committed_candidate_ids": set(),
        "total_records": len(dataset.settlement_entries),
    }
    run_store.put(result.run_id, stored)
    return _public_response(stored)


def get_run(run_id: str) -> dict[str, object] | None:
    stored = run_store.get(run_id)
    return None if stored is None else _public_response(stored)


def approve_exception(run_id: str, exception_id: str) -> dict[str, object]:
    """Reverify and transactionally apply only server-stored review context."""
    stored = _stored_run(run_id)
    result = _result(stored)
    exception = _exception(result, exception_id)
    review_contexts: dict[str, ResidualApprovalContext] = stored["review_contexts"]
    context = review_contexts.get(exception_id)
    if exception.resolution_status is not ResolutionStatus.REVIEW_REQUIRED or context is None:
        raise RunActionError(
            409,
            "EXCEPTION_NOT_APPROVABLE",
            "Only a current review-required exception with stored server context can be approved.",
        )

    state: ReconciliationState = stored["state"]
    before_state = _state_snapshot(state)
    verification_state = orchestrator.verification_state_for_packets(
        stored["packets"],
        state.unexplained_residual_paise,
        committed_candidate_ids=stored["committed_candidate_ids"],
    )
    applied = orchestrator.apply_auto_resolution(
        state,
        result.run_id,
        context.proposal,
        stored["policy"],
        verification_state,
        audit_events=result.audit_events,
        human_approved=True,
    )
    if not applied:
        raise RunActionError(
            409,
            "APPROVAL_REJECTED",
            "The stored proposal is stale, invalid, reused, or cannot preserve "
            "reconciliation invariants.",
        )

    candidate = context.proposal.candidate_resolution
    if candidate is None:
        raise RuntimeError("verified review proposal is missing its candidate")
    candidate_evidence = next(
        item.evidence
        for item in context.packet.candidates
        if item.source_id == candidate.source_id and item.candidate_id == candidate.candidate_id
    )
    financial_impact_paise = (
        state.explained_bank_credit_paise - before_state["explained_bank_credit_paise"]
    )
    result.settlement_bank_matches.append(
        DeterministicMatch(
            source_id=candidate.source_id,
            candidate_id=candidate.candidate_id,
            evidence=list(candidate_evidence),
            financial_impact_paise=financial_impact_paise,
        )
    )
    result.explained_bank_credit_paise = state.explained_bank_credit_paise
    result.unexplained_residual_paise = state.unexplained_residual_paise
    exception.resolution_status = ResolutionStatus.AUTO_RESOLVED
    del review_contexts[exception_id]
    _append_human_audit(
        result,
        exception_id,
        action="HUMAN_APPROVAL",
        decision="APPROVED",
        financial_impact_paise=financial_impact_paise,
        before_state=before_state,
        after_state=_state_snapshot(state),
    )
    return _public_response(stored)


def reject_exception(run_id: str, exception_id: str) -> dict[str, object]:
    """Reject a stored review proposal without touching financial state."""
    stored = _stored_run(run_id)
    result = _result(stored)
    exception = _exception(result, exception_id)
    review_contexts: dict[str, ResidualApprovalContext] = stored["review_contexts"]
    if exception.resolution_status is ResolutionStatus.REJECTED:
        return _public_response(stored)
    if exception.resolution_status is ResolutionStatus.AUTO_RESOLVED:
        raise RunActionError(
            409,
            "REJECTION_CONFLICT",
            "A financially applied exception cannot be rejected.",
        )
    if (
        exception.resolution_status is not ResolutionStatus.REVIEW_REQUIRED
        or exception_id not in review_contexts
    ):
        raise RunActionError(
            409,
            "EXCEPTION_NOT_REJECTABLE",
            "Only a current review-required exception with stored server context can be rejected.",
        )

    exception.resolution_status = ResolutionStatus.REJECTED
    del review_contexts[exception_id]
    state: ReconciliationState = stored["state"]
    snapshot = _state_snapshot(state)
    _append_human_audit(
        result,
        exception_id,
        action="HUMAN_REJECTION",
        decision="REJECTED",
        financial_impact_paise=0,
        before_state=snapshot,
        after_state=snapshot,
    )
    return _public_response(stored)


def get_artifact(run_id: str, artifact_name: str) -> tuple[bytes, str]:
    """Render one known artifact from active in-memory run data only."""
    stored = _stored_run(run_id)
    if artifact_name not in _ARTIFACT_NAMES:
        raise RunActionError(
            404,
            "ARTIFACT_NOT_FOUND",
            "The requested artifact is not available for this run.",
        )
    result = _result(stored)
    metrics = EvaluationReport.empty(total_records=stored["total_records"]).with_result(result)
    with TemporaryDirectory(prefix="reconra-artifact-") as temporary_directory:
        destination = Path(temporary_directory)
        writers = {
            "audit_log.json": lambda: write_audit_log(result, destination),
            "exception_worklist.csv": lambda: write_exception_worklist(result, destination),
            "reconciled_ledger.csv": lambda: write_reconciled_ledger(result, destination),
            "reconciliation_summary.json": lambda: write_reconciliation_summary(
                result, metrics, destination
            ),
        }
        content = writers[artifact_name]().read_bytes()
    return content, _ARTIFACT_CONTENT_TYPES[artifact_name]


def _stored_run(run_id: str) -> dict[str, Any]:
    stored = run_store.get(run_id)
    if stored is None:
        raise RunActionError(
            404,
            "RUN_NOT_FOUND",
            "The requested reconciliation run is unavailable or expired.",
        )
    return stored


def _result(stored: dict[str, Any]) -> ReconciliationResult:
    result = stored["result"]
    if not isinstance(result, ReconciliationResult):
        raise RuntimeError("stored run result has an invalid type")
    return result


def _exception(result: ReconciliationResult, exception_id: str) -> ReconciliationException:
    exception = next(
        (item for item in result.exceptions if item.exception_id == exception_id),
        None,
    )
    if exception is None:
        raise RunActionError(
            404,
            "EXCEPTION_NOT_FOUND",
            "The requested exception does not belong to this run.",
        )
    return exception


def _store_review_contexts(
    result: ReconciliationResult, contexts: list[ResidualApprovalContext]
) -> dict[str, ResidualApprovalContext]:
    grouped = {
        context.proposal.case_id: context
        for context in contexts
        if sum(item.proposal.case_id == context.proposal.case_id for item in contexts) == 1
    }
    for exception in result.exceptions:
        if exception.exception_id in grouped:
            exception.resolution_status = ResolutionStatus.REVIEW_REQUIRED
    return grouped


def _state_from_result(result: ReconciliationResult) -> ReconciliationState:
    state = ReconciliationState(result.total_bank_credit_paise)
    if result.explained_bank_credit_paise:
        state.commit_explanation(
            f"{result.run_id}:deterministic-explanations",
            result.explained_bank_credit_paise,
        )
    return state


def _public_response(stored: dict[str, Any]) -> dict[str, object]:
    result = _result(stored)
    metrics = EvaluationReport.empty(total_records=stored["total_records"]).with_result(result)
    return {
        "run_id": result.run_id,
        "status": "COMPLETED" if result.completed else "FAILED",
        "stages": result.stages,
        "tie_out_summary": {
            "total_bank_credit_paise": result.total_bank_credit_paise,
            "explained_bank_credit_paise": result.explained_bank_credit_paise,
            "unexplained_residual_paise": result.unexplained_residual_paise,
        },
        "metrics": {
            "resolved_records": metrics.resolved_records,
            "escalated": metrics.escalated,
            "scoring_available": metrics.scoring_available,
        },
        "exceptions": [exception.model_dump(mode="json") for exception in result.exceptions],
        "audit_events": [event.model_dump(mode="json") for event in result.audit_events],
        "artifact_names": list(_ARTIFACT_NAMES),
    }


def _state_snapshot(state: ReconciliationState) -> dict[str, int]:
    return {
        "total_bank_credit_paise": state.total_bank_credit_paise,
        "explained_bank_credit_paise": state.explained_bank_credit_paise,
        "unexplained_residual_paise": state.unexplained_residual_paise,
    }


def _append_human_audit(
    result: ReconciliationResult,
    exception_id: str,
    *,
    action: str,
    decision: str,
    financial_impact_paise: int,
    before_state: dict[str, int],
    after_state: dict[str, int],
) -> None:
    attempt = 1 + sum(
        event.run_id == result.run_id
        and event.exception_id == exception_id
        and event.action == action
        for event in result.audit_events
    )
    result.audit_events.append(
        decision_audit_event(
            run_id=result.run_id,
            event_key=f"{action.lower()}:{result.run_id}:{exception_id}:{attempt}",
            timestamp=datetime.now(UTC),
            actor="user",
            action=action,
            decision=decision,
            verification_status="VERIFIED",
            financial_impact_paise=financial_impact_paise,
            exception_id=exception_id,
            before_state=before_state,
            after_state=after_state,
            lifecycle_order=len(result.audit_events) + 1,
        )
    )
