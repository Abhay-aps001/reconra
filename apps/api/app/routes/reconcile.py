from typing import Any

from fastapi import APIRouter, Body

from app.services.reconciliation_service import reconcile_demo, reconcile_inputs

router = APIRouter(prefix="/api/reconcile", tags=["reconciliation"])


@router.post("/demo")
def reconcile_demo_route() -> dict[str, object]:
    return reconcile_demo()


@router.post("")
def reconcile_route(raw_inputs: dict[str, Any] = Body(...)) -> dict[str, object]:
    return reconcile_inputs(raw_inputs)
