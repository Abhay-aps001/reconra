import asyncio
from datetime import date

import httpx
import pytest
from reconra.evidence.builder import build_evidence_packet

from agent.providers import gemini


def _case() -> object:
    return build_evidence_packet(
        case_id="case-1",
        target_amount_paise=12_500,
        target_date=date(2026, 8, 29),
        reference_fragments=("UTR…7890",),
        candidates=(
            {
                "source_id": "settlement-1",
                "candidate_id": "setl-1",
                "amount_delta_paise": 0,
                "date_delta_days": 0,
                "utr_similarity": 0.95,
                "narration_similarity": None,
                "exact_amount": True,
                "normalized_similarity": 0.95,
                "evidence": ("normalized_utr_match",),
            },
        ),
        related_refund_count=0,
        related_adjustment_count=0,
        unresolved_reason="no deterministic unique bank match",
    )


def _transport(handler: httpx.AsyncBaseTransport) -> httpx.AsyncBaseTransport:
    return handler


def _success_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '[{"case_id":"case-1","break_class":"MANGLED_UTR",'
                                '"hypothesis":"Reference format differs.",'
                                '"candidate_resolution":{"source_id":"settlement-1","candidate_id":"setl-1"},'
                                '"confidence":0.8,"evidence":["fuzzy_utr"],'
                                '"recommended_action":"REQUEST_REVIEW"}]'
                            }
                        ]
                    }
                }
            ]
        },
    )


def test_gemini_reasoner_returns_validated_structured_proposals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fails if a valid structured provider response cannot become a typed proposal."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    transport = httpx.MockTransport(lambda request: _success_response())

    results = asyncio.run(gemini.GeminiReasoner(transport=_transport(transport)).reason([_case()]))

    assert results[0].case_id == "case-1"
    assert results[0].candidate_resolution is not None
    assert results[0].candidate_resolution.candidate_id == "setl-1"


def test_gemini_reasoner_escalates_malformed_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fails if malformed provider JSON can bypass the safe unavailable state."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"candidates": []}))

    results = asyncio.run(gemini.GeminiReasoner(transport=_transport(transport)).reason([_case()]))

    assert results[0].availability.value == "UNAVAILABLE"
    assert results[0].recommended_action.value == "ESCALATE"


def test_gemini_reasoner_escalates_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fails if a timeout escapes instead of leaving the residual safely unresolved."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    transport = httpx.MockTransport(handler)

    results = asyncio.run(gemini.GeminiReasoner(transport=_transport(transport)).reason([_case()]))

    assert results[0].availability.value == "UNAVAILABLE"


def test_gemini_reasoner_retries_rate_limit_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fails if a transient rate limit is not retried exactly once."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429) if attempts == 1 else _success_response()

    reasoner = gemini.GeminiReasoner(transport=httpx.MockTransport(handler))
    results = asyncio.run(reasoner.reason([_case()]))

    assert attempts == 2
    assert results[0].availability.value == "AVAILABLE"


def test_gemini_reasoner_stops_after_one_transient_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fails if repeated transient provider errors start an unbounded retry loop."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    reasoner = gemini.GeminiReasoner(transport=httpx.MockTransport(handler))
    results = asyncio.run(reasoner.reason([_case()]))

    assert attempts == 2
    assert results[0].availability.value == "UNAVAILABLE"


def test_gemini_reasoner_exposes_truthful_execution_status(monkeypatch: pytest.MonkeyPatch) -> None:
    """Benchmark callers need execution state, not an environment-based guess."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    reasoner = gemini.GeminiReasoner(
        transport=httpx.MockTransport(lambda request: _success_response())
    )

    asyncio.run(reasoner.reason([]))
    assert reasoner.execution_status == "NO_RESIDUALS"

    asyncio.run(reasoner.reason([_case()]))
    assert reasoner.execution_status == "LIVE_PROVIDER_INVOKED"

    failing_reasoner = gemini.GeminiReasoner(
        transport=httpx.MockTransport(lambda request: httpx.Response(503))
    )
    asyncio.run(failing_reasoner.reason([_case()]))
    assert failing_reasoner.execution_status == "PROVIDER_UNAVAILABLE"
