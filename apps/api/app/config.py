from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    environment: str = getenv("ENVIRONMENT", "development")


settings = Settings()
