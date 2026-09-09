from __future__ import annotations

import secrets
import time
from decimal import Decimal
from enum import IntEnum
from urllib.parse import quote

import requests

from config.settings import settings
from services.http_transport import BackendHttpTransport


class AccountType(IntEnum):
    CHECKING = 0
    SAVINGS = 1
    LOAN = 2


class ParabankApiClient:
    """
    Client responsible for backend test-data setup
    and REST-based validations against ParaBank.

    The HTTP transport strategy is completely
    encapsulated by BackendHttpTransport.

    This means the service layer does not need to know
    whether requests are executed:

        - directly against ParaBank;
        - through Scrape.do;
        - or using automatic fallback.
    """

    REGISTRATION_SUCCESS_MESSAGE = (
        "Your account was created successfully."
    )

    HTML_HEADERS = {
        "User-Agent": "parabank-automation-bdd/1.0",
        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "*/*;q=0.8"
        ),
    }

    FORM_HEADERS = {
        **HTML_HEADERS,
        "Content-Type": (
            "application/x-www-form-urlencoded"
        ),
    }

    JSON_HEADERS = {
        "Accept": "application/json",
    }

    def __init__(self) -> None:
        self.base_url = (
            settings.BASE_URL.rstrip("/")
        )

        self.bank_api_url = (
            settings.bank_api_url
        )

        self.transport = (
            BackendHttpTransport()
        )

    @staticmethod
    def _body_preview(
        response: requests.Response,
        limit: int = 500,
    ) -> str:
        """
        Produces a compact response body preview
        suitable for assertion/error messages.
        """

        return " ".join(
            response.text.split()
        )[:limit]

    @staticmethod
    def _json_response(
        response: requests.Response,
        operation: str,
    ):
        """
        Safely parses a JSON response.

        Instead of exposing a generic JSONDecodeError,
        this method provides useful diagnostic context
        when ParaBank or the transport returns HTML,
        XML or another unexpected payload.
        """

        try:
            return response.json()

        except ValueError as exc:
            content_type = (
                response.headers.get(
                    "Content-Type",
                    "<not informed>",
                )
            )

            transport = (
                response.headers.get(
                    "X-Test-Transport",
                    "unknown",
                )
            )

            body_preview = (
                ParabankApiClient
                ._body_preview(
                    response
                )
            )

            raise AssertionError(
                "Expected JSON response during "
                f"'{operation}', but received "
                "a different payload. "
                f"HTTP {response.status_code}. "
                f"Content-Type: {content_type}. "
                f"Transport: {transport}. "
                f"Body: {body_preview}"
            ) from exc

    @staticmethod
    def _raise_for_status(
        response: requests.Response,
        operation: str,
    ) -> None:
        """
        Adds useful context to HTTP failures instead
        of relying only on requests.raise_for_status().
        """

        if response.ok:
            return

        transport = response.headers.get(
            "X-Test-Transport",
            "unknown",
        )

        content_type = response.headers.get(
            "Content-Type",
            "<not informed>",
        )

        body_preview = (
            ParabankApiClient
            ._body_preview(
                response
            )
        )

        raise AssertionError(
            f"Backend operation '{operation}' failed. "
            f"HTTP {response.status_code}. "
            f"Transport: {transport}. "
            f"Content-Type: {content_type}. "
            f"Body: {body_preview}"
        )

    def _new_registration_session(
        self,
    ) -> requests.Session:
        """
        Creates an isolated direct HTTP session.

        Registration authenticates the newly-created
        user inside ParaBank's HTTP session, so sharing
        one registration session between scenarios can
        leak authentication/state.

        Each direct registration therefore receives its
        own requests.Session.
        """

        session = requests.Session()

        session.headers.update(
            self.HTML_HEADERS
        )

        return session

    def _validate_registration_bootstrap(
        self,
        response: requests.Response,
        transport: str,
    ) -> None:
        """
        Validates that GET /register.htm actually
        returned the ParaBank registration form.
        """

        if response.status_code >= 400:
            return

        if (
            "customer.firstName"
            not in response.text
        ):
            raise AssertionError(
                "ParaBank registration form "
                "was not available during "
                f"{transport} test-data setup. "
                f"HTTP {response.status_code}. "
                f"Body: "
                f"{self._body_preview(response)}"
            )

    def _validate_registration_response(
        self,
        response: requests.Response,
    ) -> requests.Response:
        """
        Confirms that ParaBank actually created
        the customer.

        ParaBank registration is an HTML form endpoint,
        not a REST endpoint, therefore an HTTP 200 alone
        is not enough to determine success.
        """

        transport = response.headers.get(
            "X-Test-Transport",
            "unknown",
        )

        if response.status_code >= 400:
            raise AssertionError(
                "ParaBank customer registration "
                "failed. "
                f"HTTP {response.status_code}. "
                f"Transport: {transport}. "
                f"Response: "
                f"{self._body_preview(response)}"
            )

        if (
            self.REGISTRATION_SUCCESS_MESSAGE
            not in response.text
        ):
            raise AssertionError(
                "ParaBank did not confirm "
                "customer registration. "
                f"HTTP {response.status_code}. "
                f"Transport: {transport}. "
                f"Response: "
                f"{self._body_preview(response)}"
            )

        return response

    def _register_direct(
        self,
        payload: dict[str, str],
    ) -> requests.Response:
        """
        Executes ParaBank registration directly.

        ParaBank's registration flow depends on
        HTTP session state:

            GET /register.htm
                    ↓
            session initialized
                    ↓
            POST /register.htm

        The GET and POST must use the same
        requests.Session.
        """

        registration_url = (
            f"{self.base_url}/register.htm"
        )

        session = (
            self._new_registration_session()
        )

        bootstrap_response = (
            self.transport.request_direct(
                "GET",
                registration_url,
                headers=self.HTML_HEADERS,
                session=session,
            )
        )

        if (
            bootstrap_response.status_code
            in self.transport
            .FALLBACK_STATUS_CODES
        ):
            return bootstrap_response

        self._raise_for_status(
            bootstrap_response,
            "registration bootstrap",
        )

        self._validate_registration_bootstrap(
            bootstrap_response,
            "direct",
        )

        response = (
            self.transport.request_direct(
                "POST",
                registration_url,
                data=payload,
                headers={
                    **self.FORM_HEADERS,
                    "Referer": registration_url,
                },
                session=session,
            )
        )

        return response

    def _register_proxy(
        self,
        payload: dict[str, str],
    ) -> requests.Response:
        """
        Executes the complete registration flow
        through Scrape.do.

        ParaBank registration depends on HTTP session
        state, so GET and POST must belong to the same
        target session.

        Scrape.do sessionId is used to keep the proxy
        session stable, while Scrape.do-Cookies carries
        ParaBank's target-side cookies between requests.
        """

        registration_url = (
            f"{self.base_url}/register.htm"
        )

        session_id = secrets.randbelow(
            1_000_001
        )

        bootstrap_response = (
            self.transport.request_proxy(
                "GET",
                registration_url,
                headers=self.HTML_HEADERS,
                session_id=session_id,
            )
        )

        self._raise_for_status(
            bootstrap_response,
            "proxied registration bootstrap",
        )

        self._validate_registration_bootstrap(
            bootstrap_response,
            "Scrape.do",
        )

        target_cookies = (
            bootstrap_response.headers.get(
                "Scrape.do-Cookies",
                "",
            )
        )

        if not target_cookies:
            raise AssertionError(
                "Scrape.do did not return "
                "the ParaBank session cookies "
                "required for registration."
            )

        response = (
            self.transport.request_proxy(
                "POST",
                registration_url,
                data=payload,
                headers={
                    **self.FORM_HEADERS,
                    "Referer": registration_url,
                },
                session_id=session_id,
                target_cookies=target_cookies,
            )
        )

        return response

    def register_user(
        self,
        payload: dict[str, str],
    ) -> requests.Response:
        """
        Creates a synthetic ParaBank customer.

        proxy:
            GET + POST entirely through Scrape.do.

        direct:
            GET + POST directly against ParaBank.

        auto:
            attempt complete flow directly;

            if ParaBank blocks the flow with
            HTTP 403/429, restart the COMPLETE
            registration flow through Scrape.do.

        Registration is restarted from GET because
        replaying only the POST would lose the
        HTTP-session state required by ParaBank.
        """

        if (
            self.transport.mode
            == "proxy"
        ):
            response = (
                self._register_proxy(
                    payload
                )
            )

            return (
                self
                ._validate_registration_response(
                    response
                )
            )

        direct_response = (
            self._register_direct(
                payload
            )
        )

        should_fallback = (
            self.transport.mode == "auto"
            and direct_response.status_code
            in self.transport
            .FALLBACK_STATUS_CODES
            and self.transport
            .proxy_available
        )

        if should_fallback:
            print(
                "[backend] Registration "
                "was blocked with HTTP "
                f"{direct_response.status_code}; "
                "restarting the complete "
                "registration flow through "
                "Scrape.do."
            )

            proxy_response = (
                self._register_proxy(
                    payload
                )
            )

            return (
                self
                ._validate_registration_response(
                    proxy_response
                )
            )

        return (
            self
            ._validate_registration_response(
                direct_response
            )
        )

    def login_customer(
        self,
        username: str,
        password: str,
    ) -> dict:
        """
        Authenticates a customer through ParaBank's
        REST service and returns the customer payload.
        """

        encoded_username = quote(
            username,
            safe="",
        )

        encoded_password = quote(
            password,
            safe="",
        )

        url = (
            f"{self.bank_api_url}"
            "/login/"
            f"{encoded_username}/"
            f"{encoded_password}"
        )

        response = (
            self.transport.request(
                "GET",
                url,
                headers=self.JSON_HEADERS,
            )
        )

        self._raise_for_status(
            response,
            "customer login",
        )

        customer = self._json_response(
            response,
            "customer login",
        )

        if (
            not isinstance(
                customer,
                dict,
            )
            or "id"
            not in customer
        ):
            raise AssertionError(
                "Unexpected login API "
                "response for customer "
                f"'{username}': "
                f"{customer!r}"
            )

        return customer

    def get_customer_accounts(
        self,
        customer_id: int,
    ) -> list[dict]:
        """
        Returns all accounts associated with
        the customer.
        """

        url = (
            f"{self.bank_api_url}"
            "/customers/"
            f"{customer_id}/accounts"
        )

        response = (
            self.transport.request(
                "GET",
                url,
                headers=self.JSON_HEADERS,
            )
        )

        self._raise_for_status(
            response,
            "get customer accounts",
        )

        accounts = self._json_response(
            response,
            "get customer accounts",
        )

        if not isinstance(
            accounts,
            list,
        ):
            raise AssertionError(
                "Unexpected accounts API "
                "response for customer "
                f"{customer_id}: "
                f"{accounts!r}"
            )

        if not accounts:
            raise AssertionError(
                "No accounts were returned "
                f"for customer {customer_id}."
            )

        return accounts

    def create_account(
        self,
        customer_id: int,
        account_type: AccountType,
        from_account_id: int,
    ) -> dict:
        """
        Creates another account for an existing
        ParaBank customer through REST.

        `fromAccountId` is used by ParaBank as the
        source account for the initial balance.
        """

        url = (
            f"{self.bank_api_url}"
            "/createAccount"
        )

        response = (
            self.transport.request(
                "POST",
                url,
                params={
                    "customerId": (
                        customer_id
                    ),
                    "newAccountType": int(
                        account_type
                    ),
                    "fromAccountId": (
                        from_account_id
                    ),
                },
                headers=self.JSON_HEADERS,
            )
        )

        self._raise_for_status(
            response,
            "create account",
        )

        account = self._json_response(
            response,
            "create account",
        )

        if (
            not isinstance(
                account,
                dict,
            )
            or "id"
            not in account
        ):
            raise AssertionError(
                "Unexpected create-account "
                "API response: "
                f"{account!r}"
            )

        return account

    def get_account(
        self,
        account_id: int,
    ) -> dict:
        """
        Returns one ParaBank account.
        """

        url = (
            f"{self.bank_api_url}"
            "/accounts/"
            f"{account_id}"
        )

        response = (
            self.transport.request(
                "GET",
                url,
                headers=self.JSON_HEADERS,
            )
        )

        self._raise_for_status(
            response,
            "get account",
        )

        account = self._json_response(
            response,
            "get account",
        )

        if (
            not isinstance(
                account,
                dict,
            )
            or "balance"
            not in account
        ):
            raise AssertionError(
                "Unexpected account API "
                "response for account "
                f"{account_id}: "
                f"{account!r}"
            )

        return account

    def get_account_balance(
        self,
        account_id: int,
    ) -> Decimal:
        """
        Returns an account balance as Decimal.

        Decimal is intentionally used instead of float
        because these are monetary values.
        """

        account = self.get_account(
            account_id
        )

        return Decimal(
            str(
                account["balance"]
            )
        )

    def wait_for_account_balance(
        self,
        account_id: int,
        expected_balance: Decimal,
        timeout_seconds: float = 5.0,
        polling_interval_seconds: float = 0.25,
    ) -> Decimal:
        """
        Polls the REST API until the account reaches
        the expected balance.

        This is preferable to a fixed sleep because
        execution continues immediately once the backend
        state becomes consistent.
        """

        deadline = (
            time.monotonic()
            + timeout_seconds
        )

        last_balance: Decimal | None = None

        while (
            time.monotonic()
            < deadline
        ):
            last_balance = (
                self.get_account_balance(
                    account_id
                )
            )

            if (
                last_balance
                == expected_balance
            ):
                return last_balance

            time.sleep(
                polling_interval_seconds
            )

        raise AssertionError(
            f"Account {account_id} "
            "balance did not reach "
            f"{expected_balance}. "
            "Last observed balance: "
            f"{last_balance}"
        )