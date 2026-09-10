from decimal import Decimal

from behave import (
    given,
    then,
    when,
)

from pages.register_page import RegisterPage
from services.parabank_api_client import AccountType
from utils.test_data import (
    build_customer,
    unique_username_exact,
)


@given("que estou na página de registro")
def step_open_registration(
    context,
) -> None:
    context.register_page = RegisterPage(
        context.page
    )

    context.register_page.open()


@when(
    "preencho o formulário de cadastro "
    "com dados dinâmicos válidos"
)
def step_fill_valid_registration(
    context,
) -> None:
    context.current_customer = (
        build_customer("reg")
    )

    context.register_page.fill_registration_form(
        context.current_customer.ui_data()
    )


@when(
    "preencho o formulário de cadastro "
    "com dados válidos sem informar telefone"
)
def step_fill_registration_without_phone(
    context,
) -> None:
    context.current_customer = (
        build_customer("nophone")
    )

    data = (
        context.current_customer.ui_data()
    )

    data["phone"] = ""

    context.current_customer_data = data

    context.register_page.fill_registration_form(
        data
    )


@when(
    "preencho o cadastro com username e senha "
    "de 20 caracteres"
)
def step_fill_registration_at_credential_limit(
    context,
) -> None:
    username = unique_username_exact(
        20,
        "boundary",
    )

    password = "P" * 19 + "1"

    context.current_customer = build_customer(
        "boundary",
        username=username,
        password=password,
    )

    context.register_page.fill_registration_form(
        context.current_customer.ui_data()
    )


@when(
    'preencho o formulário informando '
    'a senha "{password}" '
    'e confirmação "{confirm}"'
)
def step_fill_mismatched_password(
    context,
    password: str,
    confirm: str,
) -> None:
    context.current_customer = build_customer(
        "mismatch",
        password=password,
    )

    data = context.current_customer.ui_data()

    data["confirm_password"] = confirm

    context.register_page.fill_registration_form(
        data
    )


@given(
    "que existe um usuário previamente "
    "provisionado via backend"
)
def step_seed_user_backend(
    context,
) -> None:
    context.existing_customer = (
        build_customer("existing")
    )

    context.api_client.register_user(
        context.existing_customer
        .registration_payload()
    )


@when(
    "preencho o formulário de cadastro "
    "utilizando esse username"
)
def step_fill_with_existing_user(
    context,
) -> None:
    context.register_page.fill_registration_form(
        context.existing_customer.ui_data()
    )


@when(
    "submeto o formulário de registro"
)
def step_submit_registration(
    context,
) -> None:
    context.register_page.submit()


@then(
    "devo visualizar a mensagem "
    "de boas-vindas do usuário registrado"
)
def step_assert_registration_success(
    context,
) -> None:
    context.register_page.validate_success(
        context.current_customer.username
    )


@then(
    "os dados do novo cliente devem estar "
    "persistidos corretamente"
)
def step_assert_customer_persisted(
    context,
) -> None:
    customer = context.current_customer

    persisted = (
        context.api_client.login_customer(
            customer.username,
            customer.password,
        )
    )

    address = persisted.get("address")

    if not isinstance(address, dict):
        raise AssertionError(
            "Persisted customer did not return a valid "
            f"address payload: {persisted!r}"
        )

    expected_phone = getattr(
        context,
        "current_customer_data",
        customer.ui_data(),
    )["phone"]

    expected = {
        "firstName": customer.first_name,
        "lastName": customer.last_name,
        "phoneNumber": expected_phone,
        "ssn": customer.ssn,
    }

    actual = {
        key: persisted.get(key)
        for key in expected
    }

    if actual != expected:
        raise AssertionError(
            "Persisted customer data differs from the "
            f"registration input. Expected: {expected!r}. "
            f"Actual: {actual!r}."
        )

    expected_address = {
        "street": customer.address,
        "city": customer.city,
        "state": customer.state,
        "zipCode": customer.zip_code,
    }

    actual_address = {
        key: address.get(key)
        for key in expected_address
    }

    if actual_address != expected_address:
        raise AssertionError(
            "Persisted address differs from the registration "
            f"input. Expected: {expected_address!r}. "
            f"Actual: {actual_address!r}."
        )

    context.persisted_customer = persisted


@then(
    'o cliente deve possuir uma conta corrente '
    'inicial com saldo "{expected_balance}"'
)
def step_assert_initial_account(
    context,
    expected_balance: str,
) -> None:
    persisted = getattr(
        context,
        "persisted_customer",
        None,
    )

    if persisted is None:
        customer = context.current_customer
        persisted = context.api_client.login_customer(
            customer.username,
            customer.password,
        )

    customer_id = int(persisted["id"])

    accounts = (
        context.api_client.get_customer_accounts(
            customer_id
        )
    )

    if len(accounts) != 1:
        raise AssertionError(
            "A newly registered customer should start with "
            f"exactly one account. Actual accounts: {accounts!r}"
        )

    account = accounts[0]

    if int(account.get("type", -1)) != int(AccountType.CHECKING):
        raise AssertionError(
            "The initial customer account is not CHECKING. "
            f"Actual account: {account!r}"
        )

    actual_balance = Decimal(
        str(account.get("balance"))
    )

    if actual_balance != Decimal(expected_balance):
        raise AssertionError(
            "Unexpected initial account balance. "
            f"Expected: {expected_balance}. "
            f"Actual: {actual_balance}."
        )


@then(
    "o telefone persistido deve permanecer vazio"
)
def step_assert_optional_phone_empty(
    context,
) -> None:
    persisted = getattr(
        context,
        "persisted_customer",
        None,
    )

    if persisted is None:
        raise AssertionError(
            "Persisted customer was not captured before "
            "validating the optional phone field."
        )

    phone = persisted.get("phoneNumber")

    if phone not in ("", None):
        raise AssertionError(
            "Optional phone should remain empty after "
            f"registration. Actual value: {phone!r}"
        )


@then(
    "devo visualizar os erros de todos "
    "os campos obrigatórios do cadastro"
)
def step_assert_required_registration_errors(
    context,
) -> None:
    context.register_page\
        .validate_required_field_errors()


@then(
    'devo visualizar o erro de validação '
    'de confirmação de senha "{message}"'
)
def step_assert_password_error(
    context,
    message: str,
) -> None:
    context.register_page\
        .validate_password_mismatch_error(
            message
        )


@then(
    'devo visualizar a mensagem '
    'de erro "{message}"'
)
def step_assert_username_error(
    context,
    message: str,
) -> None:
    context.register_page\
        .validate_username_error(
            message
        )
