from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    environment: str


@router.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings.environment)
