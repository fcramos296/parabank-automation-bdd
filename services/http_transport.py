from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests

from config.settings import settings


class BackendHttpTransport:
    """Small HTTP adapter for the local ParaBank backend."""

    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "parabank-automation-bdd/1.0",
    }

    def __init__(self) -> None:
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | str | bytes | None = None,
        headers: Mapping[str, str] | None = None,
        session: requests.Session | None = None,
    ) -> requests.Response:
        """Execute one HTTP request with the configured timeout."""

        http_session = session or self.session
        return http_session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            timeout=self.timeout,
        )

    def close(self) -> None:
        """Release the transport's persistent HTTP session."""

        self.session.close()
