from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.import_service import (
    ImportServiceError,
    inspect_import,
    reconcile_import,
    validate_import,
)

router = APIRouter(prefix="/api/import", tags=["import"])


class ValidationRequest(BaseModel):
    mappings: dict[str, dict[str, str]]


@router.post("/inspect")
async def inspect_route(files: list[UploadFile] = File(...)) -> JSONResponse:
    try:
        return JSONResponse(content=await inspect_import(files))
    except ImportServiceError as error:
        return _error(error)


@router.post("/{import_id}/validate")
def validate_route(import_id: str, request: ValidationRequest) -> JSONResponse:
    try:
        return JSONResponse(content=validate_import(import_id, request.mappings))
    except ImportServiceError as error:
        return _error(error)


@router.post("/{import_id}/reconcile")
def reconcile_route(import_id: str) -> JSONResponse:
    try:
        return JSONResponse(content=reconcile_import(import_id))
    except ImportServiceError as error:
        return _error(error)


def _error(error: ImportServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "code": error.code,
            "message": "Import could not be processed safely.",
            "recoverable": True,
        },
    )
