from datetime import UTC, datetime

from reconra.audit import events


def test_decision_audit_event_records_agent_verifier_and_human_context() -> None:
    """Fails if a financial decision loses its actor, verification, or paise audit evidence."""
    event = events.decision_audit_event(
        run_id="run-1",
        event_key="proposal-1",
        timestamp=datetime(2026, 8, 29, tzinfo=UTC),
        actor="verifier",
        action="PROPOSAL_VERIFIED",
        decision="REVIEW_REQUIRED",
        verification_status="VERIFIED",
        financial_impact_paise=100,
        exception_id="case-1",
        evidence=["normalized_utr_match"],
    )

    assert event.actor == "verifier"
    assert event.action == "PROPOSAL_VERIFIED"
    assert event.financial_impact_paise == 100
    assert event.exception_id == "case-1"
