from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from app.services.reconciliation_service import (
    RunActionError,
    approve_exception,
    get_artifact,
    get_run,
    reject_exception,
)

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.get("/{run_id}")
def get_run_route(run_id: str) -> JSONResponse:
    run = get_run(run_id)
    if run is None:
        return JSONResponse(
            status_code=404,
            content={
                "code": "RUN_NOT_FOUND",
                "message": "The requested reconciliation run is unavailable or expired.",
                "recoverable": True,
            },
        )
    return JSONResponse(content=run)


@router.post("/{run_id}/exceptions/{exception_id}/approve")
def approve_exception_route(run_id: str, exception_id: str) -> JSONResponse:
    try:
        return JSONResponse(content=approve_exception(run_id, exception_id))
    except RunActionError as error:
        return _error_response(error)


@router.post("/{run_id}/exceptions/{exception_id}/reject")
def reject_exception_route(run_id: str, exception_id: str) -> JSONResponse:
    try:
        return JSONResponse(content=reject_exception(run_id, exception_id))
    except RunActionError as error:
        return _error_response(error)


@router.get("/{run_id}/artifacts/{artifact_name:path}")
def get_artifact_route(run_id: str, artifact_name: str) -> Response:
    try:
        content, media_type = get_artifact(run_id, artifact_name)
        return Response(content=content, media_type=media_type)
    except RunActionError as error:
        return _error_response(error)


def _error_response(error: RunActionError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"code": error.code, "message": error.message, "recoverable": True},
    )
