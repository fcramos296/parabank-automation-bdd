from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests

from config.settings import settings


class BackendHttpTransport:
    """
    Direct HTTP transport used by the local Docker suite.

    This branch intentionally has no proxy fallback. Both UI
    and backend traffic target the same controlled ParaBank
    instance running on localhost.
    """

    FALLBACK_STATUS_CODES = {
        403,
        429,
    }

    DEFAULT_API_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "parabank-automation-bdd/1.0",
    }

    def __init__(self) -> None:
        self.mode = "direct"
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS
        self.direct_session = requests.Session()
        self.direct_session.headers.update(
            self.DEFAULT_API_HEADERS
        )

    @property
    def proxy_available(self) -> bool:
        return False

    @staticmethod
    def _mark_transport(
        response: requests.Response,
    ) -> requests.Response:
        response.headers[
            "X-Test-Transport"
        ] = "direct"
        return response

    def request_direct(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: (
            Mapping[str, Any]
            | str
            | bytes
            | None
        ) = None,
        headers: Mapping[str, str] | None = None,
        session: requests.Session | None = None,
    ) -> requests.Response:
        http_session = (
            session
            or self.direct_session
        )

        response = http_session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            timeout=self.timeout,
        )

        return self._mark_transport(
            response
        )

    def request_proxy(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> requests.Response:
        raise RuntimeError(
            "Proxy transport is not available in the "
            "local Docker branch."
        )

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: (
            Mapping[str, Any]
            | str
            | bytes
            | None
        ) = None,
        headers: Mapping[str, str] | None = None,
    ) -> requests.Response:
        return self.request_direct(
            method,
            url,
            params=params,
            data=data,
            headers=headers,
        )
