"""Read-only Razorpay Test Mode retrieval and canonical input normalization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final

import httpx
from app.config import razorpay_settings_from_environment

_API_HOST: Final = "https://api.razorpay.com"
_COLLECTION_PAGE_SIZE: Final = 100
_RECONCILIATION_PAGE_SIZE: Final = 1_000
_DEFAULT_MAX_PAGES: Final = 100
_DEFAULT_MAX_RECONCILIATION_MONTHS: Final = 24
_READ_ONLY_PATHS: Final = frozenset(
    {
        "/v1/orders",
        "/v1/payments",
        "/v1/refunds",
        "/v1/settlements",
        "/v1/settlements/recon/combined",
    }
)


class RazorpaySyncError(RuntimeError):
    """A typed upstream failure that never retains upstream response content."""

    def __init__(self, code: str, recoverable: bool) -> None:
        super().__init__(code)
        self.code = code
        self.recoverable = recoverable


@dataclass(frozen=True)
class RazorpayService:
    """Fetch only documented GET collection endpoints from Razorpay Test Mode."""

    key_id: str
    key_secret: str
    transport: httpx.AsyncBaseTransport | None = None
    timeout_seconds: float = 10.0
    max_pages: int = _DEFAULT_MAX_PAGES
    max_reconciliation_months: int = _DEFAULT_MAX_RECONCILIATION_MONTHS

    @classmethod
    def from_environment(
        cls,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        max_pages: int = _DEFAULT_MAX_PAGES,
        max_reconciliation_months: int = _DEFAULT_MAX_RECONCILIATION_MONTHS,
    ) -> RazorpayService:
        settings = razorpay_settings_from_environment()
        return cls(
            key_id=settings.key_id,
            key_secret=settings.key_secret,
            transport=transport,
            max_pages=max_pages,
            max_reconciliation_months=max_reconciliation_months,
        )

    async def fetch_reconciliation_inputs(self) -> dict[str, object]:
        """Fetch complete bounded source collections before emitting any input data."""
        if self.max_pages < 1 or self.max_reconciliation_months < 1:
            raise ValueError("Razorpay pagination limits must be positive")
        async with httpx.AsyncClient(
            base_url=_API_HOST,
            auth=(self.key_id, self.key_secret),
            headers={"Accept": "application/json"},
            timeout=httpx.Timeout(self.timeout_seconds),
            follow_redirects=False,
            transport=self.transport,
        ) as client:
            orders = await self._fetch_collection(client, "/v1/orders", _COLLECTION_PAGE_SIZE)
            payments = await self._fetch_collection(client, "/v1/payments", _COLLECTION_PAGE_SIZE)
            refunds = await self._fetch_collection(client, "/v1/refunds", _COLLECTION_PAGE_SIZE)
            settlements = await self._fetch_collection(
                client, "/v1/settlements", _COLLECTION_PAGE_SIZE
            )
            reconciliation_rows: list[dict[str, object]] = []
            settlement_utrs = _settlement_utrs(settlements)
            months = _settlement_months(settlements)
            if len(months) > self.max_reconciliation_months:
                raise RazorpaySyncError("RAZORPAY_RECONCILIATION_WINDOW_EXCEEDED", True)
            for year, month in months:
                reconciliation_rows.extend(
                    await self._fetch_collection(
                        client,
                        "/v1/settlements/recon/combined",
                        _RECONCILIATION_PAGE_SIZE,
                        {"year": year, "month": month},
                    )
                )
        return _normalize_inputs(orders, payments, refunds, reconciliation_rows, settlement_utrs)

    async def _fetch_collection(
        self,
        client: httpx.AsyncClient,
        path: str,
        page_size: int,
        parameters: dict[str, int] | None = None,
    ) -> list[dict[str, object]]:
        if path not in _READ_ONLY_PATHS:
            raise RuntimeError("Razorpay sync attempted an unsupported endpoint")
        collected: list[dict[str, object]] = []
        for page in range(self.max_pages):
            query = {"count": page_size, "skip": page * page_size}
            if parameters is not None:
                query.update(parameters)
            try:
                response = await client.get(path, params=query)
            except httpx.TimeoutException as error:
                raise RazorpaySyncError("RAZORPAY_TIMEOUT", True) from error
            except httpx.TransportError as error:
                raise RazorpaySyncError("RAZORPAY_UNAVAILABLE", True) from error
            if response.status_code in {401, 403}:
                raise RazorpaySyncError("RAZORPAY_AUTH_FAILED", False)
            if response.status_code == 429:
                raise RazorpaySyncError("RAZORPAY_RATE_LIMITED", True)
            if response.is_error:
                raise RazorpaySyncError("RAZORPAY_UPSTREAM_FAILURE", True)
            items = _collection_items(response)
            collected.extend(items)
            if len(items) < page_size:
                return collected
        raise RazorpaySyncError("RAZORPAY_PAGINATION_LIMIT", True)


def _collection_items(response: httpx.Response) -> list[dict[str, object]]:
    try:
        payload = response.json()
    except ValueError as error:
        raise RazorpaySyncError("RAZORPAY_MALFORMED_RESPONSE", True) from error
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise RazorpaySyncError("RAZORPAY_MALFORMED_RESPONSE", True)
    items = payload["items"]
    if any(not isinstance(item, dict) for item in items):
        raise RazorpaySyncError("RAZORPAY_MALFORMED_RESPONSE", True)
    return [dict(item) for item in items]


def _settlement_utrs(settlements: list[dict[str, object]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for settlement in settlements:
        settlement_id = _required_string(settlement, "id")
        _paise(settlement, "amount")
        _paise(settlement, "fees")
        _paise(settlement, "tax")
        _timestamp(settlement, "created_at")
        utr = _optional_string(settlement, "utr")
        if utr is not None:
            result[settlement_id] = utr
    return result


def _settlement_months(settlements: list[dict[str, object]]) -> list[tuple[int, int]]:
    return sorted(
        {
            (timestamp.year, timestamp.month)
            for settlement in settlements
            for timestamp in [_timestamp(settlement, "created_at")]
        }
    )


def _normalize_inputs(
    orders: list[dict[str, object]],
    payments: list[dict[str, object]],
    refunds: list[dict[str, object]],
    reconciliation_rows: list[dict[str, object]],
    settlement_utrs: dict[str, str],
) -> dict[str, object]:
    """Use source records directly; Razorpay does not provide a bank statement feed."""
    normalized_payments = [_normalize_payment(payment) for payment in payments]
    payment_order_ids = {
        payment["payment_id"]: payment["order_id"]
        for payment in normalized_payments
        if isinstance(payment["payment_id"], str) and isinstance(payment["order_id"], str)
    }
    refund_payment_ids = _refund_payment_ids(refunds)
    normalized_reconciliation_rows = [
        _normalize_reconciliation_row(
            row,
            settlement_utrs,
            payment_order_ids,
            refund_payment_ids,
        )
        for row in reconciliation_rows
    ]
    reconciled_entity_ids = {
        row["entity_id"]
        for row in normalized_reconciliation_rows
        if isinstance(row["entity_id"], str)
    }
    normalized_reconciliation_rows.extend(
        _normalize_unsettled_refund(refund)
        for refund in refunds
        if _required_string(refund, "id") not in reconciled_entity_ids
    )
    return {
        "orders": [_normalize_order(order) for order in orders],
        "payments": normalized_payments,
        "reconciliation_rows": normalized_reconciliation_rows,
        "bank_transactions": [],
    }


def _normalize_order(order: dict[str, object]) -> dict[str, object]:
    return {
        "order_id": _required_string(order, "id"),
        "receipt": _optional_string(order, "receipt"),
        "created_at": _timestamp(order, "created_at").isoformat(),
        "amount_paise": _paise(order, "amount"),
        "currency": _currency(order),
        "status": _required_string(order, "status"),
    }


def _normalize_payment(payment: dict[str, object]) -> dict[str, object]:
    created_at = _timestamp(payment, "created_at")
    return {
        "payment_id": _required_string(payment, "id"),
        "order_id": _optional_string(payment, "order_id"),
        "amount_paise": _paise(payment, "amount"),
        "currency": _currency(payment),
        "method": _optional_string(payment, "method"),
        "captured_at": created_at.isoformat()
        if _required_string(payment, "status") == "captured"
        else None,
        "status": _required_string(payment, "status"),
    }


def _normalize_reconciliation_row(
    row: dict[str, object],
    settlement_utrs: dict[str, str],
    payment_order_ids: dict[str, str],
    refund_payment_ids: dict[str, str],
) -> dict[str, object]:
    entity_id = _required_string(row, "entity_id")
    entry_type = _required_string(row, "type")
    settlement_id = _optional_string(row, "settlement_id")
    settlement_utr = _optional_string(row, "settlement_utr")
    payment_id = _optional_string(row, "payment_id")
    if payment_id is None and entry_type == "payment":
        payment_id = entity_id
    if payment_id is None and entry_type == "refund":
        payment_id = refund_payment_ids.get(entity_id)
    order_id = _optional_string(row, "order_id")
    if order_id is None and payment_id is not None:
        order_id = payment_order_ids.get(payment_id)
    return {
        "entity_id": entity_id,
        "entry_type": entry_type,
        "debit_paise": _paise(row, "debit"),
        "credit_paise": _paise(row, "credit"),
        "amount_paise": _paise(row, "amount"),
        "fee_paise": _paise(row, "fee"),
        "tax_paise": _paise(row, "tax"),
        "created_at": _timestamp(row, "created_at").isoformat(),
        "currency": _currency(row),
        "settlement_id": settlement_id,
        "settlement_utr": settlement_utr
        if settlement_utr is not None
        else settlement_utrs.get(settlement_id) if settlement_id is not None else None,
        "payment_id": payment_id,
        "order_id": order_id,
        "order_receipt": _optional_string(row, "order_receipt"),
        "method": _optional_string(row, "method"),
    }


def _refund_payment_ids(refunds: list[dict[str, object]]) -> dict[str, str]:
    return {
        _required_string(refund, "id"): _required_string(refund, "payment_id")
        for refund in refunds
    }


def _normalize_unsettled_refund(refund: dict[str, object]) -> dict[str, object]:
    return {
        "entity_id": _required_string(refund, "id"),
        "entry_type": "refund",
        "debit_paise": _paise(refund, "amount"),
        "credit_paise": 0,
        "amount_paise": _paise(refund, "amount"),
        "fee_paise": 0,
        "tax_paise": 0,
        "created_at": _timestamp(refund, "created_at").isoformat(),
        "currency": _currency(refund),
        "settled": False,
        "payment_id": _required_string(refund, "payment_id"),
    }


def _required_string(record: dict[str, object], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise RazorpaySyncError("RAZORPAY_MALFORMED_RESPONSE", True)
    return value


def _optional_string(record: dict[str, object], field: str) -> str | None:
    value = record.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RazorpaySyncError("RAZORPAY_MALFORMED_RESPONSE", True)
    return value


def _currency(record: dict[str, object]) -> str:
    value = record.get("currency", "INR")
    if not isinstance(value, str) or not value:
        raise RazorpaySyncError("RAZORPAY_MALFORMED_RESPONSE", True)
    return value


def _paise(record: dict[str, object], field: str) -> int:
    value = record.get(field)
    if type(value) is not int or value < 0:
        raise RazorpaySyncError("RAZORPAY_MALFORMED_RESPONSE", True)
    return value


def _timestamp(record: dict[str, object], field: str) -> datetime:
    value = record.get(field)
    if type(value) is not int:
        raise RazorpaySyncError("RAZORPAY_MALFORMED_RESPONSE", True)
    try:
        return datetime.fromtimestamp(value, UTC)
    except (OverflowError, OSError, ValueError) as error:
        raise RazorpaySyncError("RAZORPAY_MALFORMED_RESPONSE", True) from error
