"""Focused red tests for the read-only Razorpay Test Mode sync service."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx
import pytest
from app.config import RazorpayConfigurationError
from app.services.razorpay_service import RazorpayService, RazorpaySyncError
from reconra.reconciliation.pipeline import CanonicalDataset


def _collection(items: list[dict[str, object]]) -> httpx.Response:
    return httpx.Response(200, json={"entity": "collection", "count": len(items), "items": items})


def _order(index: int = 1) -> dict[str, object]:
    return {
        "id": f"order_test_{index}",
        "entity": "order",
        "amount": 12_345,
        "currency": "INR",
        "receipt": f"receipt-{index}",
        "status": "paid",
        "created_at": 1_704_067_200,
    }


def _payment() -> dict[str, object]:
    return {
        "id": "pay_test_1",
        "entity": "payment",
        "order_id": "order_test_1",
        "amount": 12_345,
        "currency": "INR",
        "method": "upi",
        "status": "captured",
        "created_at": 1_704_067_200,
    }


def _refund() -> dict[str, object]:
    return {
        "id": "rfnd_test_1",
        "entity": "refund",
        "payment_id": "pay_test_1",
        "amount": 345,
        "currency": "INR",
        "status": "processed",
        "created_at": 1_704_153_600,
    }


def _settlement() -> dict[str, object]:
    return {
        "id": "setl_test_1",
        "entity": "settlement",
        "amount": 12_000,
        "fees": 290,
        "tax": 55,
        "utr": "RZRP-UTR-1",
        "status": "processed",
        "created_at": 1_704_067_200,
    }


def _recon_rows() -> list[dict[str, object]]:
    return [
        {
            "entity_id": "pay_test_1",
            "type": "payment",
            "debit": 0,
            "credit": 12_345,
            "amount": 12_345,
            "fee": 290,
            "tax": 55,
            "created_at": 1_704_067_200,
            "settlement_id": "setl_test_1",
            "payment_id": "pay_test_1",
            "order_id": "order_test_1",
            "method": "upi",
        },
        {
            "entity_id": "rfnd_test_1",
            "type": "refund",
            "debit": 345,
            "credit": 0,
            "amount": 345,
            "fee": 0,
            "tax": 0,
            "created_at": 1_704_153_600,
            "settlement_id": "setl_test_1",
            "payment_id": "pay_test_1",
        },
    ]


def _service(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    max_pages: int = 4,
) -> RazorpayService:
    monkeypatch.setenv("RAZORPAY_ENV", "test")
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_dummy_id")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "dummy-secret-not-for-output")
    return RazorpayService.from_environment(
        transport=httpx.MockTransport(handler), max_pages=max_pages
    )


def _standard_handler(request: httpx.Request) -> httpx.Response:
    responses = {
        "/v1/orders": _collection([_order()]),
        "/v1/payments": _collection([_payment()]),
        "/v1/refunds": _collection([_refund()]),
        "/v1/settlements": _collection([_settlement()]),
        "/v1/settlements/recon/combined": _collection(_recon_rows()),
    }
    return responses[request.url.path]


def test_test_mode_initializes_and_maps_official_records_to_canonical_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service(monkeypatch, _standard_handler)

    inputs = asyncio.run(service.fetch_reconciliation_inputs())

    dataset = CanonicalDataset.from_raw_inputs(inputs)
    assert dataset.orders[0].order_id == "order_test_1"
    assert dataset.payments[0].order_id == "order_test_1"
    assert all(type(record.amount_paise) is int for record in dataset.orders)
    assert all(type(record.amount_paise) is int for record in dataset.payments)
    assert len(dataset.settlement_entries) == 2
    payment_row, refund_row = dataset.settlement_entries
    assert payment_row.payment_id == "pay_test_1"
    assert payment_row.order_id == "order_test_1"
    assert payment_row.settlement_id == "setl_test_1"
    assert payment_row.settlement_utr == "RZRP-UTR-1"
    assert refund_row.entity_id == "rfnd_test_1"
    assert refund_row.payment_id == "pay_test_1"
    assert (payment_row.amount_paise, refund_row.amount_paise) == (12_345, 345)


@pytest.mark.parametrize("environment", [None, "production", "live", "unexpected", "TEST"])
def test_only_exact_test_mode_is_permitted(
    monkeypatch: pytest.MonkeyPatch, environment: str | None
) -> None:
    if environment is None:
        monkeypatch.delenv("RAZORPAY_ENV", raising=False)
    else:
        monkeypatch.setenv("RAZORPAY_ENV", environment)
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_dummy_id")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "dummy-secret-not-for-output")

    with pytest.raises(RazorpayConfigurationError, match="TEST_MODE_REQUIRED"):
        RazorpayService.from_environment()


def test_missing_credentials_fail_closed_without_echoing_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RAZORPAY_ENV", "test")
    monkeypatch.delenv("RAZORPAY_KEY_ID", raising=False)
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "dummy-secret-not-for-output")

    with pytest.raises(RazorpayConfigurationError, match="CREDENTIALS_MISSING"):
        RazorpayService.from_environment()


def test_multiple_pages_and_final_short_page_terminate(monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/orders":
            skip = int(request.url.params["skip"])
            requests.append(skip)
            if skip == 0:
                return _collection([_order(index) for index in range(skip + 1, skip + 101)])
            return _collection([_order(101)])
        return _collection([])

    inputs = asyncio.run(_service(monkeypatch, handler).fetch_reconciliation_inputs())

    assert requests == [0, 100]
    assert len(inputs["orders"]) == 101


def test_empty_account_uses_empty_canonical_collections(monkeypatch: pytest.MonkeyPatch) -> None:
    service = _service(monkeypatch, lambda _request: _collection([]))
    inputs = asyncio.run(service.fetch_reconciliation_inputs())

    assert inputs == {
        "orders": [],
        "payments": [],
        "reconciliation_rows": [],
        "bank_transactions": [],
    }


def test_unsettled_refund_is_retained_once_with_its_payment_relationship(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/refunds":
            return _collection([_refund()])
        return _collection([])

    inputs = asyncio.run(_service(monkeypatch, handler).fetch_reconciliation_inputs())

    dataset = CanonicalDataset.from_raw_inputs(inputs)
    assert len(dataset.settlement_entries) == 1
    refund = dataset.settlement_entries[0]
    assert refund.entity_id == "rfnd_test_1"
    assert refund.payment_id == "pay_test_1"
    assert refund.debit_paise == 345
    assert refund.settled is False


def test_pagination_is_bounded_and_never_loops_indefinitely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return _collection([_order(index) for index in range(100)])

    with pytest.raises(RazorpaySyncError, match="PAGINATION_LIMIT"):
        asyncio.run(_service(monkeypatch, handler, max_pages=2).fetch_reconciliation_inputs())

    assert requests == 2


def test_auth_timeout_malformed_and_partial_upstream_failures_are_typed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for response, expected_code in [
        (
            lambda _request: httpx.Response(401, text="credential detail must stay private"),
            "AUTH_FAILED",
        ),
        (lambda _request: httpx.Response(429), "RATE_LIMITED"),
        (lambda _request: (_ for _ in ()).throw(httpx.ReadTimeout("secret timeout")), "TIMEOUT"),
        (lambda _request: httpx.Response(200, json={"items": "not-a-list"}), "MALFORMED_RESPONSE"),
    ]:
        with pytest.raises(RazorpaySyncError, match=expected_code):
            asyncio.run(_service(monkeypatch, response).fetch_reconciliation_inputs())

    calls: list[str] = []

    def partial_handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/v1/orders":
            return _collection([_order()])
        return httpx.Response(503, text="do not expose this upstream response")

    with pytest.raises(RazorpaySyncError, match="UPSTREAM_FAILURE"):
        asyncio.run(_service(monkeypatch, partial_handler).fetch_reconciliation_inputs())
    assert calls == ["/v1/orders", "/v1/payments"]


def test_service_only_uses_get_against_expected_read_only_razorpay_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _standard_handler(request)

    asyncio.run(_service(monkeypatch, handler).fetch_reconciliation_inputs())

    assert {request.method for request in requests} == {"GET"}
    assert {request.url.host for request in requests} == {"api.razorpay.com"}
    assert {request.url.path for request in requests} == {
        "/v1/orders",
        "/v1/payments",
        "/v1/refunds",
        "/v1/settlements",
        "/v1/settlements/recon/combined",
    }
