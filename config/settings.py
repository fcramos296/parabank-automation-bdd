from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LOCAL_BASE_URL: str = "http://localhost:8080/parabank"
    LOCAL_STARTUP_TIMEOUT_SECONDS: float = 180.0

    HEADLESS: bool = True
    BROWSER: Literal["chromium", "firefox", "webkit"] = "chromium"

    PW_TIMEOUT_MS: int = 10_000
    PW_NAVIGATION_TIMEOUT_MS: int = 15_000
    REQUEST_TIMEOUT_SECONDS: float = 30.0

    BLOCK_NONESSENTIAL_RESOURCES: bool = True
    UI_SCENARIO_DELAY_SECONDS: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def BASE_URL(self) -> str:
        return self.LOCAL_BASE_URL.rstrip("/")

    @property
    def bank_api_url(self) -> str:
        return f"{self.BASE_URL}/services/bank"

    @model_validator(mode="after")
    def validate_configuration(self) -> "Settings":
        if not self.LOCAL_BASE_URL.strip():
            raise ValueError("LOCAL_BASE_URL cannot be empty.")

        if self.LOCAL_STARTUP_TIMEOUT_SECONDS <= 0:
            raise ValueError(
                "LOCAL_STARTUP_TIMEOUT_SECONDS must be greater than zero."
            )

        if self.PW_TIMEOUT_MS <= 0:
            raise ValueError("PW_TIMEOUT_MS must be greater than zero.")

        if self.PW_NAVIGATION_TIMEOUT_MS <= 0:
            raise ValueError(
                "PW_NAVIGATION_TIMEOUT_MS must be greater than zero."
            )

        if self.REQUEST_TIMEOUT_SECONDS <= 0:
            raise ValueError("REQUEST_TIMEOUT_SECONDS must be greater than zero.")

        if self.UI_SCENARIO_DELAY_SECONDS < 0:
            raise ValueError("UI_SCENARIO_DELAY_SECONDS cannot be negative.")

        return self


settings = Settings()
