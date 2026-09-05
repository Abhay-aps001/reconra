from app.main import app
from fastapi.testclient import TestClient


def test_demo_reconciliation_returns_real_run_contract() -> None:
    """Fails if the demo endpoint does not load the tracked input fixture and expose a run."""
    response = TestClient(app).post("/api/reconcile/demo")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"].startswith("run_")
    assert body["status"] == "COMPLETED"
    assert body["stages"]
    assert body["tie_out_summary"]["total_bank_credit_paise"] >= 0
    assert isinstance(body["metrics"], dict)
    assert isinstance(body["exceptions"], list)
    assert set(body["artifact_names"]) == {
        "audit_log.json",
        "exception_worklist.csv",
        "reconciled_ledger.csv",
        "reconciliation_summary.json",
    }
