from decimal import Decimal

from behave import (
    given,
    then,
    use_step_matcher,
    when,
)

from pages.login_page import LoginPage
from pages.transfer_page import TransferPage
from services.parabank_api_client import (
    AccountType,
)
from utils.test_data import build_customer


@given(
    "que estou autenticado com um usuário "
    "provisionado via backend e possuo "
    "duas contas"
)
def step_auth_with_two_accounts(
    context,
) -> None:
    customer = build_customer(
        "transfer"
    )

    context.api_client.register_user(
        customer.registration_payload()
    )

    customer_data = (
        context.api_client.login_customer(
            customer.username,
            customer.password,
        )
    )

    customer_id = int(
        customer_data["id"]
    )

    accounts = (
        context.api_client
        .get_customer_accounts(
            customer_id
        )
    )

    assert accounts, (
        "The provisioned customer "
        "has no account."
    )

    context.from_account_id = int(
        accounts[0]["id"]
    )

    target_account = (
        context.api_client.create_account(
            customer_id=customer_id,
            account_type=(
                AccountType.SAVINGS
            ),
            from_account_id=(
                context.from_account_id
            ),
        )
    )

    context.to_account_id = int(
        target_account["id"]
    )

    assert (
        context.from_account_id
        != context.to_account_id
    ), (
        "Transfer setup must use "
        "two different accounts."
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
        customer.username,
        customer.password,
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
            context.from_account_id,
            expected_from,
        )

    context.api_client\
        .wait_for_account_balance(
            context.to_account_id,
            expected_to,
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
            context.from_account_id,
            context.from_balance_before,
        )

    context.api_client\
        .wait_for_account_balance(
            context.to_account_id,
            context.to_balance_before,
        )