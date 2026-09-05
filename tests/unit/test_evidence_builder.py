from datetime import date

from reconra.evidence import builder


def test_build_evidence_packet_serializes_only_sanitized_deterministic_facts() -> None:
    """Fails if residual evidence admits raw customer or document data."""
    packet = builder.build_evidence_packet(
        case_id="residual-bank-001",
        target_amount_paise=12_500,
        target_date=date(2026, 8, 29),
        reference_fragments=("UTR…7890",),
        candidates=(
            {
                "source_id": "settlement-001",
                "candidate_id": "setl_001",
                "amount_delta_paise": 0,
                "date_delta_days": 1,
                "utr_similarity": 0.92,
                "narration_similarity": None,
                "exact_amount": True,
                "normalized_similarity": 0.92,
                "evidence": ("normalized_utr_match",),
            },
        ),
        related_refund_count=1,
        related_adjustment_count=0,
        unresolved_reason="no deterministic unique bank match",
    )

    serialized = packet.model_dump(mode="json")

    assert serialized == {
        "case_id": "residual-bank-001",
        "target_amount_paise": 12_500,
        "target_date": "2026-08-29",
        "reference_fragments": ["UTR…7890"],
        "candidates": [
            {
                "source_id": "settlement-001",
                "candidate_id": "setl_001",
                "amount_delta_paise": 0,
                "date_delta_days": 1,
                "utr_similarity": 0.92,
                "narration_similarity": None,
                "exact_amount": True,
                "normalized_similarity": 0.92,
                "evidence": ["normalized_utr_match"],
            }
        ],
        "related_refund_count": 1,
        "related_adjustment_count": 0,
        "unresolved_reason": "no deterministic unique bank match",
    }
    serialized_text = str(serialized).lower()
    assert "email" not in serialized_text
    assert "phone" not in serialized_text
    assert "account" not in serialized_text
    assert "raw_pdf" not in serialized_text
