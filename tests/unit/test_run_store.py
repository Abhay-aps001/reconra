from app.services import run_store


def test_run_store_evicts_oldest_entry_after_twenty_runs() -> None:
    """Fails if in-memory run state grows beyond the approved cap."""
    store = run_store.RunStore(max_entries=20)
    for index in range(21):
        store.put(f"run-{index}", {"index": index})

    assert store.get("run-0") is None
    assert store.get("run-20") == {"index": 20}


def test_run_store_expires_entries_after_thirty_minutes(monkeypatch) -> None:
    """Fails if an in-memory run survives beyond the approved TTL."""
    clock = iter((0.0, 0.0, 1_800.0))
    monkeypatch.setattr(run_store, "monotonic", lambda: next(clock))
    store = run_store.RunStore()
    store.put("run-1", {"value": 1})

    assert store.get("run-1") is None
