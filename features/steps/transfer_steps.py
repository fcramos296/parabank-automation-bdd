from decimal import Decimal

from behave import (
    given,
    then,
    use_step_matcher,
    when,
)

from config.settings import settings
from pages.login_page import LoginPage
from pages.transfer_page import TransferPage


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

    context.to_balance_before = (
        context.api_client
        .get_account_balance(
            context.to_account_id
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
    "os saldos das duas contas devem "
    "refletir a transferência"
)
def step_assert_balances_after_transfer(
    context,
) -> None:
    expected_from = (
        context.from_balance_before
        - context.transferred_amount
    )

    expected_to = (
        context.to_balance_before
        + context.transferred_amount
    )

    context.api_client\
        .wait_for_account_balance(
            account_id=(
                context.from_account_id
            ),
            expected_balance=(
                expected_from
            ),
        )

    context.api_client\
        .wait_for_account_balance(
            account_id=(
                context.to_account_id
            ),
            expected_balance=(
                expected_to
            ),
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


@then(
    "os saldos das duas contas devem "
    "permanecer inalterados"
)
def step_assert_balances_unchanged(
    context,
) -> None:
    context.api_client\
        .wait_for_account_balance(
            account_id=(
                context.from_account_id
            ),
            expected_balance=(
                context.from_balance_before
            ),
        )

    context.api_client\
        .wait_for_account_balance(
            account_id=(
                context.to_account_id
            ),
            expected_balance=(
                context.to_balance_before
            ),
        )
