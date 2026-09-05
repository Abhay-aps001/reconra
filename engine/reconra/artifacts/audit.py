"""Export complete deterministic decision-audit records."""

from __future__ import annotations

from json import dumps
from pathlib import Path

from reconra.models.result import ReconciliationResult


def write_audit_log(result: ReconciliationResult, destination: Path) -> Path:
    """Write audit events in deterministic financial-decision chronology."""
    path = destination / "audit_log.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        event.model_dump(mode="json")
        for event in sorted(
            result.audit_events,
            key=lambda item: (item.timestamp, item.lifecycle_order, item.event_id),
        )
    ]
    path.write_text(
        dumps(rows, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path
