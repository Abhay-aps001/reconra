"""Focused API tests for the Razorpay Test Mode sync boundary."""

from __future__ import annotations

import pytest
from app.main import app
from app.services import reconciliation_service
from app.services.razorpay_service import RazorpaySyncError
from app.services.run_store import RunStore
from fastapi.testclient import TestClient


class _NoopReasoner:
    async def reason(self, cases: object) -> list[object]:
        return []


class _ReadOnlyFakeService:
    async def fetch_reconciliation_inputs(self) -> dict[str, object]:
        return {
            "orders": [],
            "payments": [],
            "reconciliation_rows": [],
            "bank_transactions": [],
        }


class _ConfiguredFakeService:
    @classmethod
    def from_environment(cls) -> _ReadOnlyFakeService:
        return _ReadOnlyFakeService()


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(reconciliation_service, "run_store", RunStore())
    monkeypatch.setattr(reconciliation_service, "GeminiReasoner", _NoopReasoner)
    with TestClient(app) as test_client:
        yield test_client


def test_sync_creates_a_normal_authoritative_reconra_run_and_stores_it(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.routes import razorpay as razorpay_route

    monkeypatch.setattr(razorpay_route, "RazorpayService", _ConfiguredFakeService)

    response = client.post("/api/razorpay/sync")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"].startswith("run_")
    stored = reconciliation_service.run_store.get(body["run_id"])
    assert stored is not None
    assert stored["result"].run_id == body["run_id"]
    assert "review_contexts" not in body


def test_sync_rejects_missing_or_non_test_environment_with_typed_safe_error(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("RAZORPAY_ENV", raising=False)
    monkeypatch.delenv("RAZORPAY_KEY_ID", raising=False)
    monkeypatch.delenv("RAZORPAY_KEY_SECRET", raising=False)

    response = client.post("/api/razorpay/sync")

    assert response.status_code == 403
    assert response.json() == {
        "code": "RAZORPAY_TEST_MODE_REQUIRED",
        "message": "Razorpay sync is available only when RAZORPAY_ENV=test.",
        "recoverable": False,
    }


def test_sync_sanitizes_service_error_and_never_exposes_environment_credentials(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.routes import razorpay as razorpay_route

    secret = "dummy-secret-not-for-output"

    class _FailingService:
        @classmethod
        def from_environment(cls) -> _FailingService:
            return cls()

        async def fetch_reconciliation_inputs(self) -> dict[str, object]:
            raise RazorpaySyncError("RAZORPAY_UPSTREAM_FAILURE", True)

    monkeypatch.setattr(razorpay_route, "RazorpayService", _FailingService)
    monkeypatch.setenv("RAZORPAY_ENV", "test")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_dummy_id")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", secret)

    response = client.post("/api/razorpay/sync")

    assert response.status_code == 503
    assert response.json() == {
        "code": "RAZORPAY_UPSTREAM_FAILURE",
        "message": "Razorpay sync could not be completed safely.",
        "recoverable": True,
    }
    assert secret not in response.text
    assert secret not in str(reconciliation_service.run_store._runs)


def test_existing_manual_reconciliation_endpoint_remains_available(client: TestClient) -> None:
    response = client.post(
        "/api/reconcile",
        json={"orders": [], "payments": [], "reconciliation_rows": [], "bank_transactions": []},
    )

    assert response.status_code == 200
    assert response.json()["run_id"].startswith("run_")
