from collections import OrderedDict
from time import monotonic
from typing import Any


class ImportStore:
    def __init__(self, ttl_seconds: int = 30 * 60, max_entries: int = 20) -> None:
        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._imports: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()

    def put(self, import_id: str, value: dict[str, Any]) -> None:
        self._purge()
        self._imports[import_id] = (monotonic(), value)
        while len(self._imports) > self._max_entries:
            self._imports.popitem(last=False)

    def get(self, import_id: str) -> dict[str, Any] | None:
        self._purge()
        entry = self._imports.get(import_id)
        return None if entry is None else entry[1]

    def _purge(self) -> None:
        now = monotonic()
        for key, (created, _) in list(self._imports.items()):
            if now - created >= self._ttl_seconds:
                del self._imports[key]
