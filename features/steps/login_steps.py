from behave import (
    given,
    then,
    use_step_matcher,
    when,
)

from pages.login_page import LoginPage
from utils.test_data import (
    build_customer,
    unique_username,
)


@given("que estou na tela de login")
def step_open_login(context) -> None:
    context.login_page = LoginPage(
        context.page
    )

    context.login_page.open()


@given(
    "que existe um usuário registrado "
    "via backend com credenciais válidas"
)
def step_create_valid_user_via_backend(
    context,
) -> None:
    context.seeded_customer = (
        build_customer("login")
    )

    context.api_client.register_user(
        context.seeded_customer
        .registration_payload()
    )


@when(
    "informo o usuário e senha cadastrados"
)
def step_login_with_seeded_credentials(
    context,
) -> None:
    context.login_page.login(
        context.seeded_customer.username,
        context.seeded_customer.password,
    )


use_step_matcher("re")


@when(
    r'realizo login com usuário '
    r'"(?P<username>.*)" e senha '
    r'"(?P<password>.*)"'
)
def step_login_with_params(
    context,
    username: str,
    password: str,
) -> None:
    if username == "inexistente":
        username_to_use = (
            unique_username("invalid")
        )
    else:
        username_to_use = username

    context.login_page.login(
        username_to_use,
        password,
    )


use_step_matcher("parse")


@then(
    "sou direcionado para a tela "
    "de visão geral da conta"
)
def step_validate_login_success(
    context,
) -> None:
    context.login_page.validate_login_success()


@then(
    'devo visualizar a mensagem de erro '
    'de autenticação "{error_message}"'
)
def step_validate_login_failure(
    context,
    error_message: str,
) -> None:
    context.login_page.validate_login_failure(
        error_message
    )