from fastapi import HTTPException
from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str
    recoverable: bool


def api_error(status_code: int, code: str, message: str, recoverable: bool) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ApiError(code=code, message=message, recoverable=recoverable).model_dump(),
    )
