from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    BASE_URL: str = (
        "https://parabank.parasoft.com/parabank"
    )

    HEADLESS: bool = True

    BROWSER: Literal[
        "chromium",
        "firefox",
        "webkit",
    ] = "chromium"

    PW_TIMEOUT_MS: int = 10_000

    PW_NAVIGATION_TIMEOUT_MS: int = 15_000

    REQUEST_TIMEOUT_SECONDS: float = 30.0

    BACKEND_TRANSPORT: Literal[
        "direct",
        "proxy",
        "auto",
    ] = "proxy"

    BROWSER_TRANSPORT: Literal[
        "direct",
        "proxy",
    ] = "direct"

    BLOCK_NONESSENTIAL_RESOURCES: bool = True

    UI_SCENARIO_DELAY_SECONDS: float = 2.0

    PUBLIC_EXISTING_USERNAME: str = "john"

    PUBLIC_EXISTING_PASSWORD: SecretStr = (
        SecretStr("demo")
    )

    SCRAPE_DO_TOKEN: SecretStr | None = None

    SCRAPE_DO_API_URL: str = (
        "https://api.scrape.do/"
    )

    SCRAPE_DO_PROXY_URL: str = (
        "http://proxy.scrape.do:8080"
    )

    SCRAPE_DO_BROWSER_PROXY_PARAMS: str = (
        "render=false"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def bank_api_url(self) -> str:
        return (
            f"{self.BASE_URL.rstrip('/')}"
            "/services/bank"
        )

    @property
    def public_existing_password(
        self,
    ) -> str:
        return (
            self.PUBLIC_EXISTING_PASSWORD
            .get_secret_value()
            .strip()
        )

    @property
    def scrape_do_token(
        self,
    ) -> str | None:
        if self.SCRAPE_DO_TOKEN is None:
            return None

        value = (
            self.SCRAPE_DO_TOKEN
            .get_secret_value()
            .strip()
        )

        return value or None

    @model_validator(mode="after")
    def validate_configuration(
        self,
    ) -> "Settings":
        proxy_required = (
            self.BACKEND_TRANSPORT == "proxy"
            or self.BROWSER_TRANSPORT == "proxy"
        )

        if (
            proxy_required
            and not self.scrape_do_token
        ):
            raise ValueError(
                "SCRAPE_DO_TOKEN is required "
                "when a Scrape.do transport "
                "is enabled."
            )

        if not self.PUBLIC_EXISTING_USERNAME.strip():
            raise ValueError(
                "PUBLIC_EXISTING_USERNAME "
                "cannot be empty."
            )

        if not self.public_existing_password:
            raise ValueError(
                "PUBLIC_EXISTING_PASSWORD "
                "cannot be empty."
            )

        if self.REQUEST_TIMEOUT_SECONDS <= 0:
            raise ValueError(
                "REQUEST_TIMEOUT_SECONDS "
                "must be greater than zero."
            )

        if self.UI_SCENARIO_DELAY_SECONDS < 0:
            raise ValueError(
                "UI_SCENARIO_DELAY_SECONDS "
                "cannot be negative."
            )

        return self


settings = Settings()
