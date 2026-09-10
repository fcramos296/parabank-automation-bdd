from __future__ import annotations

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
    """Backend test-data setup and REST validations for local ParaBank."""

    REGISTRATION_SUCCESS_MESSAGE = "Your account was created successfully."

    HTML_HEADERS = {
        "User-Agent": "parabank-automation-bdd/1.0",
        "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
    }

    FORM_HEADERS = {
        **HTML_HEADERS,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    JSON_HEADERS = {"Accept": "application/json"}

    def __init__(self) -> None:
        self.base_url = settings.BASE_URL.rstrip("/")
        self.bank_api_url = settings.bank_api_url
        self.transport = BackendHttpTransport()

    @staticmethod
    def _body_preview(response: requests.Response, limit: int = 500) -> str:
        """Return a compact response preview for diagnostic messages."""

        return " ".join(response.text.split())[:limit]

    @classmethod
    def _json_response(cls, response: requests.Response, operation: str):
        """Parse JSON and raise an assertion with HTTP context on failure."""

        try:
            return response.json()
        except ValueError as exc:
            content_type = response.headers.get("Content-Type", "<not informed>")
            raise AssertionError(
                f"Expected JSON response during '{operation}', but received a "
                f"different payload. HTTP {response.status_code}. "
                f"Content-Type: {content_type}. "
                f"Body: {cls._body_preview(response)}"
            ) from exc

    @classmethod
    def _raise_for_status(cls, response: requests.Response, operation: str) -> None:
        """Raise a diagnostic assertion for unsuccessful backend responses."""

        if response.ok:
            return

        content_type = response.headers.get("Content-Type", "<not informed>")
        raise AssertionError(
            f"Backend operation '{operation}' failed. "
            f"HTTP {response.status_code}. "
            f"Content-Type: {content_type}. "
            f"Body: {cls._body_preview(response)}"
        )

    def _new_registration_session(self) -> requests.Session:
        """Create an isolated session for ParaBank's stateful registration flow."""

        session = requests.Session()
        session.headers.update(self.HTML_HEADERS)
        return session

    def _validate_registration_bootstrap(self, response: requests.Response) -> None:
        """Confirm that GET /register.htm returned the registration form."""

        self._raise_for_status(response, "registration bootstrap")

        if "customer.firstName" not in response.text:
            raise AssertionError(
                "ParaBank registration form was not available during test-data "
                f"setup. HTTP {response.status_code}. "
                f"Body: {self._body_preview(response)}"
            )

    def _validate_registration_response(
        self,
        response: requests.Response,
    ) -> requests.Response:
        """Confirm that the registration form actually created the customer."""

        self._raise_for_status(response, "customer registration")

        if self.REGISTRATION_SUCCESS_MESSAGE not in response.text:
            raise AssertionError(
                "ParaBank did not confirm customer registration. "
                f"HTTP {response.status_code}. "
                f"Response: {self._body_preview(response)}"
            )

        return response

    def register_user(self, payload: dict[str, str]) -> requests.Response:
        """Create a customer through ParaBank's HTML registration flow.

        Registration depends on server-side HTTP session state, therefore
        GET /register.htm and POST /register.htm intentionally share the same
        isolated requests.Session.
        """

        registration_url = f"{self.base_url}/register.htm"

        with self._new_registration_session() as session:
            bootstrap_response = self.transport.request(
                "GET",
                registration_url,
                headers=self.HTML_HEADERS,
                session=session,
            )
            self._validate_registration_bootstrap(bootstrap_response)

            response = self.transport.request(
                "POST",
                registration_url,
                data=payload,
                headers={**self.FORM_HEADERS, "Referer": registration_url},
                session=session,
            )
            return self._validate_registration_response(response)

    def login_customer(self, username: str, password: str) -> dict:
        """Authenticate a customer through ParaBank's REST API."""

        encoded_username = quote(username, safe="")
        encoded_password = quote(password, safe="")
        url = f"{self.bank_api_url}/login/{encoded_username}/{encoded_password}"

        response = self.transport.request("GET", url, headers=self.JSON_HEADERS)
        self._raise_for_status(response, "customer login")
        customer = self._json_response(response, "customer login")

        if not isinstance(customer, dict) or "id" not in customer:
            raise AssertionError(
                f"Unexpected login API response for customer '{username}': {customer!r}"
            )

        return customer

    def get_customer_accounts(self, customer_id: int) -> list[dict]:
        """Return every account associated with a customer."""

        url = f"{self.bank_api_url}/customers/{customer_id}/accounts"
        response = self.transport.request("GET", url, headers=self.JSON_HEADERS)
        self._raise_for_status(response, "get customer accounts")
        accounts = self._json_response(response, "get customer accounts")

        if not isinstance(accounts, list):
            raise AssertionError(
                "Unexpected accounts API response for customer "
                f"{customer_id}: {accounts!r}"
            )

        if not accounts:
            raise AssertionError(
                f"No accounts were returned for customer {customer_id}."
            )

        return accounts

    def create_account(
        self,
        customer_id: int,
        account_type: AccountType,
        from_account_id: int,
    ) -> dict:
        """Create another account for an existing ParaBank customer."""

        url = f"{self.bank_api_url}/createAccount"
        response = self.transport.request(
            "POST",
            url,
            params={
                "customerId": customer_id,
                "newAccountType": int(account_type),
                "fromAccountId": from_account_id,
            },
            headers=self.JSON_HEADERS,
        )
        self._raise_for_status(response, "create account")
        account = self._json_response(response, "create account")

        if not isinstance(account, dict) or "id" not in account:
            raise AssertionError(f"Unexpected create-account API response: {account!r}")

        return account

    def get_account(self, account_id: int) -> dict:
        """Return one ParaBank account."""

        url = f"{self.bank_api_url}/accounts/{account_id}"
        response = self.transport.request("GET", url, headers=self.JSON_HEADERS)
        self._raise_for_status(response, "get account")
        account = self._json_response(response, "get account")

        if not isinstance(account, dict) or "balance" not in account:
            raise AssertionError(
                f"Unexpected account API response for account {account_id}: {account!r}"
            )

        return account

    def get_account_transactions(self, account_id: int) -> list[dict]:
        """Return all transactions associated with an account."""

        url = f"{self.bank_api_url}/accounts/{account_id}/transactions"
        response = self.transport.request("GET", url, headers=self.JSON_HEADERS)
        self._raise_for_status(response, "get account transactions")
        transactions = self._json_response(response, "get account transactions")

        if not isinstance(transactions, list):
            raise AssertionError(
                "Unexpected transactions API response for account "
                f"{account_id}: {transactions!r}"
            )

        return transactions

    def get_account_balance(self, account_id: int) -> Decimal:
        """Return an account balance as Decimal to preserve monetary precision."""

        account = self.get_account(account_id)
        return Decimal(str(account["balance"]))

    def wait_for_account_balance(
        self,
        account_id: int,
        expected_balance: Decimal,
        timeout_seconds: float = 5.0,
        polling_interval_seconds: float = 0.25,
    ) -> Decimal:
        """Poll until an account reaches the expected balance."""

        deadline = time.monotonic() + timeout_seconds
        last_balance: Decimal | None = None

        while time.monotonic() < deadline:
            last_balance = self.get_account_balance(account_id)

            if last_balance == expected_balance:
                return last_balance

            time.sleep(polling_interval_seconds)

        raise AssertionError(
            f"Account {account_id} balance did not reach {expected_balance}. "
            f"Last observed balance: {last_balance}"
        )

    def close(self) -> None:
        """Release persistent HTTP resources used by the API client."""

        self.transport.close()
