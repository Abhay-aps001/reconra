from __future__ import annotations

import pytest
from app.main import app
from app.services import reconciliation_service
from app.services.import_store import ImportStore
from app.services.run_store import RunStore
from fastapi.testclient import TestClient


def test_import_requires_confirmation_before_existing_reconciliation_pipeline(monkeypatch) -> None:
    monkeypatch.setattr(reconciliation_service, "run_store", RunStore())
    from app.services import import_service

    monkeypatch.setattr(import_service, "import_store", ImportStore())
    client = TestClient(app)
    content = b"Txn Date,Narration,Deposit Amt,Ref No\n2026-09-01,Settlement,123.45,UTR-1\n"
    inspection = client.post(
        "/api/import/inspect", files=[("files", ("bank.csv", content, "text/csv"))]
    )
    assert inspection.status_code == 200
    import_id = inspection.json()["import_id"]
    assert client.post(f"/api/import/{import_id}/reconcile").status_code == 409
    validated = client.post(
        f"/api/import/{import_id}/validate",
        json={
            "mappings": {
                "bank.csv": {
                    "Txn Date": "transaction_date",
                    "Narration": "description",
                    "Deposit Amt": "credit_paise",
                    "Ref No": "utr",
                }
            }
        },
    )
    assert validated.status_code == 200
    reconciled = client.post(f"/api/import/{import_id}/reconcile")
    assert reconciled.status_code == 200
    assert reconciliation_service.run_store.get(reconciled.json()["run_id"]) is not None


def test_import_rejects_xlsm_traversal_and_scanned_pdf() -> None:
    client = TestClient(app)
    for name, content, expected in [
        ("book.xlsm", b"not-a-workbook", "UNSUPPORTED_FILE_TYPE"),
        ("../escape.csv", b"a\n1\n", "INVALID_FILENAME"),
        ("scan.pdf", b"%PDF-1.4\n% image only\n", "PDF_TEXT_TABLE_REQUIRED"),
    ]:
        response = client.post(
            "/api/import/inspect", files=[("files", (name, content, "application/octet-stream"))]
        )
        assert response.status_code == 400
        assert response.json()["code"] == expected


@pytest.mark.parametrize(
    ("columns", "values", "mapping"),
    [
        (
            "Txn Date,Narration,Deposit Amt,Ref No",
            "not-a-date,Settlement,123.45,UTR-1",
            {
                "Txn Date": "transaction_date",
                "Narration": "description",
                "Deposit Amt": "credit_paise",
                "Ref No": "utr",
            },
        ),
        (
            "Order ID,Created At,Amount,Status",
            "order-1,not-a-datetime,123.45,paid",
            {
                "Order ID": "order_id",
                "Created At": "created_at",
                "Amount": "amount_paise",
                "Status": "status",
            },
        ),
    ],
)
def test_invalid_date_or_datetime_is_a_typed_validation_failure_and_cannot_reconcile(
    columns: str, values: str, mapping: dict[str, str]
) -> None:
    client = TestClient(app)
    inspection = client.post(
        "/api/import/inspect",
        files=[("files", ("input.csv", f"{columns}\n{values}\n", "text/csv"))],
    )
    import_id = inspection.json()["import_id"]
    validation = client.post(
        f"/api/import/{import_id}/validate", json={"mappings": {"input.csv": mapping}}
    )
    assert validation.status_code == 400
    assert validation.json()["code"] == "INVALID_MAPPING_VALUE"
    assert client.post(f"/api/import/{import_id}/reconcile").status_code == 409
