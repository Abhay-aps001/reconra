from __future__ import annotations

from dataclasses import replace

import pytest
from app.main import app
from app.services import reconciliation_service
from app.services.run_store import RunStore
from fastapi.testclient import TestClient
from reconra.models.exception import ResolutionStatus
from reconra.reconciliation.state import ReconciliationState

from agent.schemas.proposal import AgentProposal


class _ReviewReasoner:
    async def reason(self, cases):
        packet = next((packet for packet in cases if packet.candidates), None)
        if packet is None:
            return []
        candidate = packet.candidates[0]
        return [
            AgentProposal(
                case_id=packet.case_id,
                break_class="MANGLED_UTR",
                hypothesis="The reference format differs.",
                candidate_resolution={
                    "source_id": candidate.source_id,
                    "candidate_id": candidate.candidate_id,
                },
                confidence=0.8,
                evidence=["fuzzy_utr"],
                recommended_action="REQUEST_REVIEW",
            )
        ]


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(reconciliation_service, "run_store", RunStore())
    monkeypatch.setattr(reconciliation_service, "GeminiReasoner", _ReviewReasoner)
    with TestClient(app) as test_client:
        yield test_client


def _review_inputs() -> dict[str, object]:
    return {
        "orders": [],
        "payments": [],
        "reconciliation_rows": [
            {
                "entity_id": "entry-NVR-1",
                "settlement_id": "setl-NVR-1",
                "settlement_utr": "UTR-2026-ABC-12345",
                "type": "payment",
                "credit": 100_000,
                "debit": 0,
                "amount": 100_000,
                "fee": 0,
                "tax": 0,
                "created_at": "2026-08-30T00:00:00+00:00",
                "settled_at": "2026-08-30T00:00:00+00:00",
                "description": "Razorpay settlement Acme Stores",
            }
        ],
        "bank_transactions": [
            {
                "bank_transaction_id": "bank-NVR-1",
                "transaction_date": "2026-08-31",
                "description": "Acme Stores Razorpay settlement",
                "utr": "UTR 2026 ABC 1234",
                "credit_paise": 100_000,
                "debit_paise": 0,
            }
        ],
    }


def _review_run(client: TestClient) -> tuple[str, str, dict[str, object]]:
    response = client.post("/api/reconcile", json=_review_inputs())
    assert response.status_code == 200
    run = response.json()
    exception = next(
        item
        for item in run["exceptions"]
        if item["resolution_status"] == "REVIEW_REQUIRED"
    )
    return run["run_id"], exception["exception_id"], run


def _approve_url(run_id: str, exception_id: str) -> str:
    return f"/api/runs/{run_id}/exceptions/{exception_id}/approve"


def _reject_url(run_id: str, exception_id: str) -> str:
    return f"/api/runs/{run_id}/exceptions/{exception_id}/reject"


def test_approve_uses_server_stored_review_context_and_preserves_conservation(
    client: TestClient,
) -> None:
    run_id, exception_id, before = _review_run(client)

    response = client.post(_approve_url(run_id, exception_id))

    assert response.status_code == 200
    after = response.json()
    assert after["tie_out_summary"] == {
        "total_bank_credit_paise": 100_000,
        "explained_bank_credit_paise": 100_000,
        "unexplained_residual_paise": 0,
    }
    exception = next(item for item in after["exceptions"] if item["exception_id"] == exception_id)
    assert exception["resolution_status"] == "AUTO_RESOLVED"
    assert after["tie_out_summary"]["explained_bank_credit_paise"] == (
        before["tie_out_summary"]["explained_bank_credit_paise"] + 100_000
    )
    assert any(
        event["actor"] == "user"
        and event["action"] == "HUMAN_APPROVAL"
        and event["exception_id"] == exception_id
        for event in after["audit_events"]
    )


def test_approve_rejects_unknown_run_and_exception(client: TestClient) -> None:
    run_id, _, _ = _review_run(client)

    unknown_run = client.post(_approve_url("run-not-found", "exception-not-found"))
    unknown_exception = client.post(_approve_url(run_id, "exception-not-found"))

    assert unknown_run.status_code == 404
    assert unknown_run.json()["code"] == "RUN_NOT_FOUND"
    assert unknown_exception.status_code == 404
    assert unknown_exception.json()["code"] == "EXCEPTION_NOT_FOUND"


def test_escalated_exception_without_stored_review_context_cannot_be_approved(
    client: TestClient,
) -> None:
    response = client.post("/api/reconcile/demo")
    assert response.status_code == 200
    run = response.json()
    exception = next(item for item in run["exceptions"] if item["resolution_status"] == "ESCALATED")

    approval = client.post(_approve_url(run["run_id"], exception["exception_id"]))

    assert approval.status_code == 409
    assert approval.json()["code"] == "EXCEPTION_NOT_APPROVABLE"


def test_approve_rejects_stale_or_reused_server_context_without_money_mutation(
    client: TestClient,
) -> None:
    run_id, exception_id, before = _review_run(client)
    stored = reconciliation_service.run_store.get(run_id)
    assert stored is not None
    stored["result"].exceptions[0].resolution_status = ResolutionStatus.ESCALATED

    stale = client.post(_approve_url(run_id, exception_id))

    assert stale.status_code == 409
    assert stale.json()["code"] == "EXCEPTION_NOT_APPROVABLE"
    assert client.get(f"/api/runs/{run_id}").json()["tie_out_summary"] == before["tie_out_summary"]

    run_id, exception_id, before = _review_run(client)
    stored = reconciliation_service.run_store.get(run_id)
    assert stored is not None
    context = stored["review_contexts"][exception_id]
    candidate = context.proposal.candidate_resolution
    assert candidate is not None
    stored["committed_candidate_ids"].add(candidate.candidate_id)

    reused = client.post(_approve_url(run_id, exception_id))

    assert reused.status_code == 409
    assert reused.json()["code"] == "APPROVAL_REJECTED"
    assert client.get(f"/api/runs/{run_id}").json()["tie_out_summary"] == before["tie_out_summary"]


def test_approve_reverification_failure_and_conservation_failure_do_not_partially_mutate(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_id, exception_id, before = _review_run(client)
    stored = reconciliation_service.run_store.get(run_id)
    assert stored is not None
    context = stored["review_contexts"][exception_id]
    stored["review_contexts"][exception_id] = replace(
        context,
        proposal=context.proposal.model_copy(update={"evidence": ["not-in-packet"]}),
    )

    failed_verification = client.post(_approve_url(run_id, exception_id))

    assert failed_verification.status_code == 409
    assert failed_verification.json()["code"] == "APPROVAL_REJECTED"
    assert client.get(f"/api/runs/{run_id}").json()["tie_out_summary"] == before["tie_out_summary"]

    run_id, exception_id, before = _review_run(client)
    monkeypatch.setattr(
        ReconciliationState,
        "_assert_money_conservation",
        lambda self: (_ for _ in ()).throw(RuntimeError("forced")),
    )

    failed_conservation = client.post(_approve_url(run_id, exception_id))

    assert failed_conservation.status_code == 409
    assert failed_conservation.json()["code"] == "APPROVAL_REJECTED"
    assert client.get(f"/api/runs/{run_id}").json()["tie_out_summary"] == before["tie_out_summary"]


def test_approve_is_idempotent_and_ignores_client_proposal_payload(client: TestClient) -> None:
    run_id, exception_id, _ = _review_run(client)
    injected = {
        "candidate_resolution": {"source_id": "attacker", "candidate_id": "attacker"},
        "recommended_action": "AUTO_RESOLVE",
    }

    first = client.post(_approve_url(run_id, exception_id), json=injected)
    second = client.post(_approve_url(run_id, exception_id))

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["code"] == "EXCEPTION_NOT_APPROVABLE"
    current = client.get(f"/api/runs/{run_id}").json()
    assert current["tie_out_summary"]["explained_bank_credit_paise"] == 100_000


def test_reject_marks_review_context_without_financial_mutation_or_repeat_effect(
    client: TestClient,
) -> None:
    run_id, exception_id, before = _review_run(client)

    first = client.post(_reject_url(run_id, exception_id))
    second = client.post(_reject_url(run_id, exception_id))

    assert first.status_code == 200
    assert second.status_code == 200
    after = second.json()
    exception = next(item for item in after["exceptions"] if item["exception_id"] == exception_id)
    assert exception["resolution_status"] == "REJECTED"
    assert after["tie_out_summary"] == before["tie_out_summary"]
    assert len(
        [event for event in after["audit_events"] if event["action"] == "HUMAN_REJECTION"]
    ) == 1


def test_reject_handles_unknowns_and_conflicts_after_approval(client: TestClient) -> None:
    run_id, exception_id, _ = _review_run(client)

    unknown_run = client.post(_reject_url("run-not-found", exception_id))
    unknown_exception = client.post(_reject_url(run_id, "exception-not-found"))
    assert unknown_run.status_code == 404
    assert unknown_run.json()["code"] == "RUN_NOT_FOUND"
    assert unknown_exception.status_code == 404
    assert unknown_exception.json()["code"] == "EXCEPTION_NOT_FOUND"

    assert client.post(_approve_url(run_id, exception_id)).status_code == 200
    conflict = client.post(_reject_url(run_id, exception_id))
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "REJECTION_CONFLICT"


@pytest.mark.parametrize(
    ("artifact_name", "content_type"),
    [
        ("reconciled_ledger.csv", "text/csv"),
        ("exception_worklist.csv", "text/csv"),
        ("reconciliation_summary.json", "application/json"),
        ("audit_log.json", "application/json"),
    ],
)
def test_artifacts_are_generated_from_the_requested_stored_run(
    client: TestClient, artifact_name: str, content_type: str
) -> None:
    run_id, _, _ = _review_run(client)

    response = client.get(f"/api/runs/{run_id}/artifacts/{artifact_name}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(content_type)
    assert response.content


def test_artifacts_reject_unknown_runs_invalid_names_and_path_traversal(client: TestClient) -> None:
    run_id, _, _ = _review_run(client)

    unknown_run = client.get("/api/runs/run-not-found/artifacts/audit_log.json")
    invalid = client.get(f"/api/runs/{run_id}/artifacts/not-an-artifact.txt")
    traversal = client.get(f"/api/runs/{run_id}/artifacts/%2E%2E%2Fsecrets.txt")

    assert unknown_run.status_code == 404
    assert unknown_run.json()["code"] == "RUN_NOT_FOUND"
    assert invalid.status_code == 404
    assert invalid.json()["code"] == "ARTIFACT_NOT_FOUND"
    assert traversal.status_code == 404
    assert traversal.json()["code"] == "ARTIFACT_NOT_FOUND"


def test_review_context_is_internal_and_separate_runs_do_not_share_it(client: TestClient) -> None:
    first_run_id, first_exception_id, first = _review_run(client)
    second_run_id, second_exception_id, second = _review_run(client)

    assert first_run_id != second_run_id
    assert first_exception_id == second_exception_id
    assert "review_contexts" not in first
    assert "review_contexts" not in second
    first_stored = reconciliation_service.run_store.get(first_run_id)
    second_stored = reconciliation_service.run_store.get(second_run_id)
    assert first_stored is not None and second_stored is not None
    assert first_stored["review_contexts"] is not second_stored["review_contexts"]
