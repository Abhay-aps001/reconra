import asyncio
from datetime import date

from reconra.evidence.builder import build_evidence_packet

from agent.providers import gemini


def test_no_gemini_key_keeps_residual_reasoning_safely_disabled(monkeypatch) -> None:
    """Fails if deterministic-only operation requires a Gemini credential."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    case = build_evidence_packet(
        case_id="case-1",
        target_amount_paise=1,
        target_date=date(2026, 8, 29),
        reference_fragments=(),
        candidates=(),
        related_refund_count=0,
        related_adjustment_count=0,
        unresolved_reason="missing candidate",
    )

    results = asyncio.run(gemini.GeminiReasoner().reason([case]))

    assert results[0].availability.value == "UNAVAILABLE"
