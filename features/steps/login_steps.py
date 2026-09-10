from behave import (
    given,
    then,
    use_step_matcher,
    when,
)

from config.settings import settings
from pages.login_page import LoginPage
from utils.test_data import unique_username


@given("que estou na tela de login")
def step_open_login(
    context,
) -> None:
    context.login_page = LoginPage(
        context.page
    )

    context.login_page.open()


@given(
    "que possuo credenciais válidas de um "
    "usuário existente no ambiente público"
)
def step_use_existing_public_user(
    context,
) -> None:
    context.login_username = (
        settings.PUBLIC_EXISTING_USERNAME
    )

    context.login_password = (
        settings.public_existing_password
    )


@when(
    "informo as credenciais válidas "
    "desse usuário"
)
def step_login_with_existing_credentials(
    context,
) -> None:
    context.login_page.login(
        context.login_username,
        context.login_password,
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
            unique_username(
                "invalid"
            )
        )
    else:
        username_to_use = username

    context.login_page.login(
        username_to_use,
        password,
    )


use_step_matcher("parse")


@then(
    "devo estar autenticado e "
    "visualizar os serviços da conta"
)
def step_validate_login_success(
    context,
) -> None:
    context.login_page.validate_login_success()


@then(
    "a tentativa de autenticação deve ser "
    "rejeitada com uma mensagem de erro"
)
def step_validate_invalid_login(
    context,
) -> None:
    context.login_page.validate_unauthenticated_with_error()


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
