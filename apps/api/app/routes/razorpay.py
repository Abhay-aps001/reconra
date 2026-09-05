"""Razorpay Test Mode read-only synchronization endpoint."""

import asyncio

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import RazorpayConfigurationError
from app.schemas.razorpay import RazorpaySyncErrorResponse
from app.services.razorpay_service import RazorpayService, RazorpaySyncError
from app.services.reconciliation_service import reconcile_inputs

router = APIRouter(prefix="/api/razorpay", tags=["razorpay"])


@router.post("/sync")
def razorpay_sync_route() -> JSONResponse:
    """Read complete Test Mode data, then enter the ordinary reconciliation service."""
    try:
        inputs = asyncio.run(RazorpayService.from_environment().fetch_reconciliation_inputs())
    except RazorpayConfigurationError as error:
        return _configuration_error_response(error)
    except RazorpaySyncError as error:
        return _sync_error_response(error)
    return JSONResponse(content=reconcile_inputs(inputs))


def _configuration_error_response(error: RazorpayConfigurationError) -> JSONResponse:
    if error.code == "RAZORPAY_TEST_MODE_REQUIRED":
        response = RazorpaySyncErrorResponse(
            code=error.code,
            message="Razorpay sync is available only when RAZORPAY_ENV=test.",
            recoverable=False,
        )
        return JSONResponse(status_code=403, content=response.model_dump())
    response = RazorpaySyncErrorResponse(
        code=error.code,
        message="Razorpay sync credentials are unavailable in the server environment.",
        recoverable=False,
    )
    return JSONResponse(status_code=503, content=response.model_dump())


def _sync_error_response(error: RazorpaySyncError) -> JSONResponse:
    status_code = 502 if error.code == "RAZORPAY_AUTH_FAILED" else 503
    response = RazorpaySyncErrorResponse(
        code=error.code,
        message="Razorpay sync could not be completed safely.",
        recoverable=error.recoverable,
    )
    return JSONResponse(status_code=status_code, content=response.model_dump())
