"""Safe public error contract for the Razorpay sync boundary."""

from pydantic import BaseModel


class RazorpaySyncErrorResponse(BaseModel):
    code: str
    message: str
    recoverable: bool
