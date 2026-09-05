from app.main import app
from fastapi.testclient import TestClient


def test_general_reconcile_stores_and_retrieves_a_run() -> None:
    """Fails if normal input reconciliation cannot be retrieved from volatile run state."""
    client = TestClient(app)
    demo = client.post("/api/reconcile/demo").json()

    response = client.get(f"/api/runs/{demo['run_id']}")

    assert response.status_code == 200
    assert response.json()["run_id"] == demo["run_id"]


def test_unknown_run_returns_typed_error() -> None:
    """Fails if missing volatile runs return an untyped framework response."""
    response = TestClient(app).get("/api/runs/not-a-run")

    assert response.status_code == 404
    assert response.json() == {
        "code": "RUN_NOT_FOUND",
        "message": "The requested reconciliation run is unavailable or expired.",
        "recoverable": True,
    }
