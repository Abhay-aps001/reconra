"""Short-lived, non-durable reconciliation run storage."""

from collections import OrderedDict
from time import monotonic
from typing import Any


class RunStore:
    def __init__(self, ttl_seconds: int = 30 * 60, max_entries: int = 20) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._runs: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()

    def put(self, run_id: str, value: dict[str, Any]) -> None:
        self._purge_expired()
        self._runs[run_id] = (monotonic(), value)
        self._runs.move_to_end(run_id)
        while len(self._runs) > self._max_entries:
            self._runs.popitem(last=False)

    def get(self, run_id: str) -> dict[str, Any] | None:
        self._purge_expired()
        entry = self._runs.get(run_id)
        return None if entry is None else entry[1]

    def _purge_expired(self) -> None:
        now = monotonic()
        for run_id, (created, _) in list(self._runs.items()):
            if now - created >= self._ttl_seconds:
                del self._runs[run_id]
