from behave import (
    given,
    then,
    when,
)

from pages.register_page import RegisterPage
from utils.test_data import build_customer


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

    context.register_page.fill_registration_form(
        data
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
    customer = build_customer(
        "mismatch",
        password=password,
    )

    data = customer.ui_data()

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
