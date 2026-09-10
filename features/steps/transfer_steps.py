import time
from decimal import Decimal
from typing import Any

from behave import (
    given,
    then,
    use_step_matcher,
    when,
)

from config.settings import settings
from pages.login_page import LoginPage
from pages.transfer_page import TransferPage


TRANSFER_SENT_DESCRIPTION = "Funds Transfer Sent"
TRANSFER_RECEIVED_DESCRIPTION = "Funds Transfer Received"
TRANSFER_TRANSACTION_TIMEOUT_SECONDS = 8.0
TRANSFER_TRANSACTION_POLL_SECONDS = 0.5


def _account_balance(
    account: dict,
) -> Decimal:
    try:
        return Decimal(
            str(
                account["balance"]
            )
        )
    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise AssertionError(
            "Unexpected account payload "
            f"without a valid balance: {account!r}"
        ) from exc


def _select_existing_accounts(
    accounts: list[dict],
) -> tuple[dict, dict]:
    if len(accounts) < 2:
        raise AssertionError(
            "The configured public customer must "
            "have at least two existing accounts."
        )

    try:
        source = max(
            accounts,
            key=lambda account: (
                _account_balance(account),
                int(account["id"]),
            ),
        )

        remaining = [
            account
            for account in accounts
            if int(account["id"])
            != int(source["id"])
        ]

        target = max(
            remaining,
            key=lambda account: int(
                account["id"]
            ),
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        raise AssertionError(
            "Unexpected account payload returned "
            "for the configured public customer: "
            f"{accounts!r}"
        ) from exc

    return source, target


def _get_account_transactions(
    context,
    account_id: int,
) -> list[dict[str, Any]]:
    url = (
        f"{context.api_client.bank_api_url}"
        f"/accounts/{account_id}/transactions"
    )

    response = (
        context.api_client.transport.request(
            "GET",
            url,
            headers=(
                context.api_client.JSON_HEADERS
            ),
        )
    )

    if not response.ok:
        transport = response.headers.get(
            "X-Test-Transport",
            "unknown",
        )

        body = " ".join(
            response.text.split()
        )[:300]

        raise AssertionError(
            "Unable to retrieve transactions for "
            f"account {account_id}. "
            f"HTTP {response.status_code}. "
            f"Transport: {transport}. "
            f"Body: {body}"
        )

    try:
        transactions = response.json()
    except ValueError as exc:
        raise AssertionError(
            "Transactions endpoint did not return "
            f"JSON for account {account_id}."
        ) from exc

    if not isinstance(
        transactions,
        list,
    ):
        raise AssertionError(
            "Unexpected transactions payload for "
            f"account {account_id}: "
            f"{transactions!r}"
        )

    return transactions


def _transaction_ids(
    transactions: list[dict[str, Any]],
) -> set[int]:
    ids: set[int] = set()

    for transaction in transactions:
        try:
            ids.add(
                int(
                    transaction["id"]
                )
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            raise AssertionError(
                "Unexpected transaction payload "
                f"without a valid id: {transaction!r}"
            ) from exc

    return ids


def _matches_transfer_transaction(
    transaction: dict[str, Any],
    *,
    account_id: int,
    amount: Decimal,
    transaction_type: str,
    description: str,
) -> bool:
    try:
        transaction_amount = Decimal(
            str(
                transaction["amount"]
            )
        )

        return (
            int(transaction["accountId"])
            == account_id
            and transaction_amount == amount
            and str(transaction["type"])
            == transaction_type
            and str(transaction["description"])
            == description
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        return False


def _find_new_transfer_transaction(
    transactions: list[dict[str, Any]],
    *,
    previous_ids: set[int],
    account_id: int,
    amount: Decimal,
    transaction_type: str,
    description: str,
) -> dict[str, Any] | None:
    for transaction in transactions:
        try:
            transaction_id = int(
                transaction["id"]
            )
        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

        if transaction_id in previous_ids:
            continue

        if _matches_transfer_transaction(
            transaction,
            account_id=account_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
        ):
            return transaction

    return None


def _wait_for_transfer_transactions(
    context,
) -> None:
    deadline = (
        time.monotonic()
        + TRANSFER_TRANSACTION_TIMEOUT_SECONDS
    )

    last_source_transactions: list[
        dict[str, Any]
    ] = []

    last_target_transactions: list[
        dict[str, Any]
    ] = []

    while time.monotonic() < deadline:
        last_source_transactions = (
            _get_account_transactions(
                context,
                context.from_account_id,
            )
        )

        last_target_transactions = (
            _get_account_transactions(
                context,
                context.to_account_id,
            )
        )

        debit = (
            _find_new_transfer_transaction(
                last_source_transactions,
                previous_ids=(
                    context
                    .source_transaction_ids_before
                ),
                account_id=(
                    context.from_account_id
                ),
                amount=(
                    context.transferred_amount
                ),
                transaction_type="Debit",
                description=(
                    TRANSFER_SENT_DESCRIPTION
                ),
            )
        )

        credit = (
            _find_new_transfer_transaction(
                last_target_transactions,
                previous_ids=(
                    context
                    .target_transaction_ids_before
                ),
                account_id=(
                    context.to_account_id
                ),
                amount=(
                    context.transferred_amount
                ),
                transaction_type="Credit",
                description=(
                    TRANSFER_RECEIVED_DESCRIPTION
                ),
            )
        )

        if (
            debit is not None
            and credit is not None
        ):
            context.transfer_debit = debit
            context.transfer_credit = credit
            return

        time.sleep(
            TRANSFER_TRANSACTION_POLL_SECONDS
        )

    source_new_ids = sorted(
        _transaction_ids(
            last_source_transactions
        )
        - context.source_transaction_ids_before
    )

    target_new_ids = sorted(
        _transaction_ids(
            last_target_transactions
        )
        - context.target_transaction_ids_before
    )

    raise AssertionError(
        "The UI reported a successful transfer, "
        "but the expected new Debit/Credit records "
        "were not observed through the backend. "
        f"Source account: {context.from_account_id}. "
        f"Target account: {context.to_account_id}. "
        f"Amount: {context.transferred_amount}. "
        f"New source transaction ids: {source_new_ids}. "
        f"New target transaction ids: {target_new_ids}."
    )


@given(
    "que estou autenticado com um usuário "
    "existente do ambiente público e possuo "
    "duas contas"
)
def step_auth_with_two_accounts(
    context,
) -> None:
    username = (
        settings.PUBLIC_EXISTING_USERNAME
    )

    password = (
        settings.public_existing_password
    )

    customer_data = (
        context.api_client.login_customer(
            username,
            password,
        )
    )

    customer_id = int(
        customer_data["id"]
    )

    context.transfer_customer_id = (
        customer_id
    )

    accounts = (
        context.api_client
        .get_customer_accounts(
            customer_id
        )
    )

    (
        source_account,
        target_account,
    ) = _select_existing_accounts(
        accounts
    )

    context.from_account_id = int(
        source_account["id"]
    )

    context.to_account_id = int(
        target_account["id"]
    )

    context.from_balance_before = (
        context.api_client
        .get_account_balance(
            context.from_account_id
        )
    )

    login_page = LoginPage(
        context.page
    )

    login_page.open()

    login_page.login(
        username,
        password,
    )

    login_page.validate_login_success()


@given(
    "navego para a tela "
    "de transferência de fundos"
)
def step_navigate_to_transfer(
    context,
) -> None:
    context.transfer_page = TransferPage(
        context.page
    )

    context.transfer_page.open()


@when(
    'realizo a transferência da quantia '
    'de "{amount}" entre contas distintas'
)
def step_transfer_funds(
    context,
    amount: str,
) -> None:
    context.transferred_amount = Decimal(
        amount
    )

    if (
        context.from_balance_before
        < context.transferred_amount
    ):
        raise AssertionError(
            "The selected public source account "
            "does not have enough balance for "
            f"the transfer. Account: "
            f"{context.from_account_id}. "
            f"Balance: {context.from_balance_before}. "
            f"Required: {context.transferred_amount}."
        )

    source_transactions_before = (
        _get_account_transactions(
            context,
            context.from_account_id,
        )
    )

    target_transactions_before = (
        _get_account_transactions(
            context,
            context.to_account_id,
        )
    )

    context.source_transaction_ids_before = (
        _transaction_ids(
            source_transactions_before
        )
    )

    context.target_transaction_ids_before = (
        _transaction_ids(
            target_transactions_before
        )
    )

    context.transfer_page.transfer(
        amount=amount,
        from_account_id=(
            context.from_account_id
        ),
        to_account_id=(
            context.to_account_id
        ),
    )


@then(
    'a transferência deve ser concluída '
    'exibindo o valor "{amount}" '
    "e as contas envolvidas"
)
def step_assert_transfer_success(
    context,
    amount: str,
) -> None:
    context.transfer_page\
        .validate_transfer_success(
            expected_amount=amount,
            from_account_id=(
                context.from_account_id
            ),
            to_account_id=(
                context.to_account_id
            ),
        )


@then(
    "os lançamentos de débito e crédito devem "
    "registrar a transferência"
)
def step_assert_transfer_transactions(
    context,
) -> None:
    _wait_for_transfer_transactions(
        context
    )


use_step_matcher("re")


@when(
    r'realizo a tentativa de transferência '
    r'com valor "(?P<amount>.*)"'
)
def step_attempt_invalid_transfer(
    context,
    amount: str,
) -> None:
    context.transfer_page.transfer(
        amount=amount,
        from_account_id=(
            context.from_account_id
        ),
        to_account_id=(
            context.to_account_id
        ),
    )


use_step_matcher("parse")


@then(
    'o sistema deve apresentar o erro '
    'de transferência "{message}"'
)
def step_assert_transfer_error(
    context,
    message: str,
) -> None:
    context.transfer_page\
        .validate_transfer_error(
            message
        )
