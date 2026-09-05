from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    environment: str = getenv("ENVIRONMENT", "development")


settings = Settings()


class RazorpayConfigurationError(RuntimeError):
    """Safe configuration failure for the Test Mode-only integration."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class RazorpaySettings:
    key_id: str
    key_secret: str


def razorpay_settings_from_environment() -> RazorpaySettings:
    """Read Test Mode credentials only at the server-side sync boundary."""
    if getenv("RAZORPAY_ENV") != "test":
        raise RazorpayConfigurationError("RAZORPAY_TEST_MODE_REQUIRED")
    key_id = getenv("RAZORPAY_KEY_ID")
    key_secret = getenv("RAZORPAY_KEY_SECRET")
    if not key_id or not key_secret:
        raise RazorpayConfigurationError("RAZORPAY_CREDENTIALS_MISSING")
    return RazorpaySettings(key_id=key_id, key_secret=key_secret)
