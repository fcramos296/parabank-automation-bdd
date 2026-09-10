import time
from decimal import Decimal
from typing import Any

from behave import given, then, when

from pages.login_page import LoginPage
from pages.transfer_page import TransferPage
from services.parabank_api_client import AccountType
from utils.test_data import build_customer


TRANSFER_SENT_DESCRIPTION = "Funds Transfer Sent"
TRANSFER_RECEIVED_DESCRIPTION = "Funds Transfer Received"
TRANSFER_TRANSACTION_TIMEOUT_SECONDS = 8.0
TRANSFER_TRANSACTION_POLL_SECONDS = 0.5
NEGATIVE_STABILIZATION_SECONDS = 2.0
NEGATIVE_POLL_SECONDS = 0.25
EMPTY_VALUE = "[vazio]"


def _account_balance(account: dict) -> Decimal:
    try:
        return Decimal(str(account["balance"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise AssertionError(
            f"Unexpected account payload without a valid balance: {account!r}"
        ) from exc


def _select_source_account(accounts: list[dict]) -> dict:
    if not accounts:
        raise AssertionError("The newly registered customer has no account.")

    try:
        return max(
            accounts,
            key=lambda account: (
                _account_balance(account),
                int(account["id"]),
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise AssertionError(
            f"Unexpected account payload returned for the new customer: {accounts!r}"
        ) from exc


def _transaction_ids(transactions: list[dict[str, Any]]) -> set[int]:
    ids: set[int] = set()

    for transaction in transactions:
        try:
            ids.add(int(transaction["id"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise AssertionError(
                "Unexpected transaction payload without a valid id: "
                f"{transaction!r}"
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
        transaction_amount = Decimal(str(transaction["amount"]))
        return (
            int(transaction["accountId"]) == account_id
            and transaction_amount == amount
            and str(transaction["type"]) == transaction_type
            and str(transaction["description"]) == description
        )
    except (KeyError, TypeError, ValueError):
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
            transaction_id = int(transaction["id"])
        except (KeyError, TypeError, ValueError):
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


def _capture_transfer_state(
    context,
    *,
    from_account_id: int,
    to_account_id: int,
) -> None:
    context.from_account_id = from_account_id
    context.to_account_id = to_account_id
    context.from_balance_before = context.api_client.get_account_balance(
        from_account_id
    )
    context.to_balance_before = context.api_client.get_account_balance(to_account_id)

    source_transactions = context.api_client.get_account_transactions(from_account_id)
    target_transactions = context.api_client.get_account_transactions(to_account_id)

    context.source_transaction_ids_before = _transaction_ids(source_transactions)
    context.target_transaction_ids_before = _transaction_ids(target_transactions)


def _execute_transfer(
    context,
    *,
    amount: str,
    from_account_id: int,
    to_account_id: int,
) -> None:
    _capture_transfer_state(
        context,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
    )
    context.transferred_amount = Decimal(amount)
    context.transferred_amount_display = amount

    context.transfer_page.transfer(
        amount=amount,
        from_account_id=from_account_id,
        to_account_id=to_account_id,
    )


def _wait_for_transfer_transactions(context) -> None:
    deadline = time.monotonic() + TRANSFER_TRANSACTION_TIMEOUT_SECONDS
    last_source_transactions: list[dict[str, Any]] = []
    last_target_transactions: list[dict[str, Any]] = []

    while time.monotonic() < deadline:
        last_source_transactions = context.api_client.get_account_transactions(
            context.from_account_id
        )
        last_target_transactions = context.api_client.get_account_transactions(
            context.to_account_id
        )

        debit = _find_new_transfer_transaction(
            last_source_transactions,
            previous_ids=context.source_transaction_ids_before,
            account_id=context.from_account_id,
            amount=context.transferred_amount,
            transaction_type="Debit",
            description=TRANSFER_SENT_DESCRIPTION,
        )
        credit = _find_new_transfer_transaction(
            last_target_transactions,
            previous_ids=context.target_transaction_ids_before,
            account_id=context.to_account_id,
            amount=context.transferred_amount,
            transaction_type="Credit",
            description=TRANSFER_RECEIVED_DESCRIPTION,
        )

        if debit is not None and credit is not None:
            context.transfer_debit = debit
            context.transfer_credit = credit
            return

        time.sleep(TRANSFER_TRANSACTION_POLL_SECONDS)

    source_new_ids = sorted(
        _transaction_ids(last_source_transactions)
        - context.source_transaction_ids_before
    )
    target_new_ids = sorted(
        _transaction_ids(last_target_transactions)
        - context.target_transaction_ids_before
    )

    raise AssertionError(
        "The UI reported a successful transfer, but the expected new "
        "Debit/Credit records were not observed. "
        f"Source account: {context.from_account_id}. "
        f"Target account: {context.to_account_id}. "
        f"Amount: {context.transferred_amount}. "
        f"New source transaction ids: {source_new_ids}. "
        f"New target transaction ids: {target_new_ids}."
    )


def _assert_transactions_unchanged_during_stabilization(context) -> None:
    """Observe rejected transfers for a bounded window before asserting absence."""

    deadline = time.monotonic() + NEGATIVE_STABILIZATION_SECONDS

    while True:
        source_ids = _transaction_ids(
            context.api_client.get_account_transactions(context.from_account_id)
        )
        target_ids = _transaction_ids(
            context.api_client.get_account_transactions(context.to_account_id)
        )

        if source_ids != context.source_transaction_ids_before:
            raise AssertionError(
                "Rejected transfer created or changed a source-account "
                "transaction. "
                f"Before: {sorted(context.source_transaction_ids_before)}. "
                f"After: {sorted(source_ids)}."
            )

        if target_ids != context.target_transaction_ids_before:
            raise AssertionError(
                "Rejected transfer created or changed a target-account "
                "transaction. "
                f"Before: {sorted(context.target_transaction_ids_before)}. "
                f"After: {sorted(target_ids)}."
            )

        if time.monotonic() >= deadline:
            return

        time.sleep(NEGATIVE_POLL_SECONDS)


@given("que estou autenticado com um usuário exclusivo e possuo duas contas")
def step_auth_with_two_accounts(context) -> None:
    customer = build_customer("transfer")
    context.transfer_customer = customer

    context.api_client.register_user(customer.registration_payload())
    customer_data = context.api_client.login_customer(
        customer.username,
        customer.password,
    )
    customer_id = int(customer_data["id"])
    context.transfer_customer_id = customer_id

    existing_accounts = context.api_client.get_customer_accounts(customer_id)
    source_account = _select_source_account(existing_accounts)
    primary_account_id = int(source_account["id"])

    secondary_account = context.api_client.create_account(
        customer_id=customer_id,
        account_type=AccountType.SAVINGS,
        from_account_id=primary_account_id,
    )

    context.primary_account_id = primary_account_id
    context.secondary_account_id = int(secondary_account["id"])

    login_page = LoginPage(context.page)
    login_page.open()
    login_page.login(customer.username, customer.password)
    login_page.validate_login_success()


@given("que existe uma conta pertencente a outro cliente")
def step_create_foreign_account(context) -> None:
    foreign_customer = build_customer("foreign")
    context.api_client.register_user(foreign_customer.registration_payload())
    persisted = context.api_client.login_customer(
        foreign_customer.username,
        foreign_customer.password,
    )
    foreign_accounts = context.api_client.get_customer_accounts(int(persisted["id"]))
    context.foreign_account_id = int(foreign_accounts[0]["id"])


@given("navego para a tela de transferência de fundos")
def step_navigate_to_transfer(context) -> None:
    context.transfer_page = TransferPage(context.page)
    context.transfer_page.open()


@when('realizo a transferência da quantia de "{amount}" entre contas distintas')
def step_transfer_funds(context, amount: str) -> None:
    _execute_transfer(
        context,
        amount=amount,
        from_account_id=context.primary_account_id,
        to_account_id=context.secondary_account_id,
    )


@when(
    'realizo a transferência da quantia de "{amount}" '
    "da segunda conta para a primeira"
)
def step_transfer_reverse_direction(context, amount: str) -> None:
    _execute_transfer(
        context,
        amount=amount,
        from_account_id=context.secondary_account_id,
        to_account_id=context.primary_account_id,
    )


@when("transfiro todo o saldo disponível da conta de origem")
def step_transfer_full_balance(context) -> None:
    source_balance = context.api_client.get_account_balance(context.primary_account_id)
    amount = f"{source_balance:.2f}"

    _execute_transfer(
        context,
        amount=amount,
        from_account_id=context.primary_account_id,
        to_account_id=context.secondary_account_id,
    )


@when('realizo a tentativa de transferência com valor "{amount}"')
def step_attempt_invalid_transfer(context, amount: str) -> None:
    normalized_amount = "" if amount == EMPTY_VALUE else amount
    _capture_transfer_state(
        context,
        from_account_id=context.primary_account_id,
        to_account_id=context.secondary_account_id,
    )
    context.transfer_page.transfer(
        amount=normalized_amount,
        from_account_id=context.from_account_id,
        to_account_id=context.to_account_id,
    )


@then(
    'a transferência deve ser concluída exibindo o valor "{amount}" '
    "e as contas envolvidas"
)
def step_assert_transfer_success(context, amount: str) -> None:
    context.transfer_page.validate_transfer_success(
        expected_amount=amount,
        from_account_id=context.from_account_id,
        to_account_id=context.to_account_id,
    )


@then("a transferência do saldo total deve ser concluída entre as contas")
def step_assert_full_balance_transfer_success(context) -> None:
    context.transfer_page.validate_transfer_success(
        expected_amount=context.transferred_amount_display,
        from_account_id=context.from_account_id,
        to_account_id=context.to_account_id,
    )


@then("os lançamentos de débito e crédito devem registrar a transferência")
def step_assert_transfer_transactions(context) -> None:
    _wait_for_transfer_transactions(context)


@then("os saldos das duas contas devem refletir a transferência")
def step_assert_balances_after_transfer(context) -> None:
    expected_from = context.from_balance_before - context.transferred_amount
    expected_to = context.to_balance_before + context.transferred_amount

    context.api_client.wait_for_account_balance(
        account_id=context.from_account_id,
        expected_balance=expected_from,
    )
    context.api_client.wait_for_account_balance(
        account_id=context.to_account_id,
        expected_balance=expected_to,
    )


@then("a conta de origem deve ficar com saldo zero")
def step_assert_source_balance_zero(context) -> None:
    balance = context.api_client.get_account_balance(context.from_account_id)

    if balance != Decimal("0.00"):
        raise AssertionError(
            "Source account should have zero balance after the full-balance "
            f"transfer. Actual: {balance}."
        )


@then("os seletores devem listar somente as contas do cliente autenticado")
def step_assert_only_customer_accounts_visible(context) -> None:
    expected_accounts = {
        context.primary_account_id,
        context.secondary_account_id,
    }
    context.transfer_page.validate_account_options(
        expected_account_ids=expected_accounts,
        forbidden_account_ids={context.foreign_account_id},
    )


@then("a transferência deve ser rejeitada sem confirmação de sucesso")
def step_assert_transfer_rejected(context) -> None:
    context.transfer_page.validate_transfer_rejected()


@then("nenhuma transação deve ser criada para a tentativa rejeitada")
def step_assert_no_transaction_created(context) -> None:
    _assert_transactions_unchanged_during_stabilization(context)


@then("os saldos das duas contas devem permanecer inalterados")
def step_assert_balances_unchanged(context) -> None:
    source_balance = context.api_client.get_account_balance(context.from_account_id)
    target_balance = context.api_client.get_account_balance(context.to_account_id)

    if source_balance != context.from_balance_before:
        raise AssertionError(
            "Rejected transfer changed the source-account balance. "
            f"Expected: {context.from_balance_before}. Actual: {source_balance}."
        )

    if target_balance != context.to_balance_before:
        raise AssertionError(
            "Rejected transfer changed the target-account balance. "
            f"Expected: {context.to_balance_before}. Actual: {target_balance}."
        )
