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
def step_open_login(
    context,
) -> None:
    context.login_page = LoginPage(
        context.page
    )

    context.login_page.open()


@given(
    "que existe um usuário exclusivo "
    "cadastrado para autenticação"
)
def step_seed_exclusive_login_user(
    context,
) -> None:
    context.login_customer = (
        build_customer("login")
    )

    context.api_client.register_user(
        context.login_customer
        .registration_payload()
    )

    context.login_username = (
        context.login_customer.username
    )

    context.login_password = (
        context.login_customer.password
    )


@when(
    "informo as credenciais válidas "
    "desse usuário"
)
def step_login_with_valid_credentials(
    context,
) -> None:
    context.login_page.login(
        context.login_username,
        context.login_password,
    )


@when(
    'realizo login com esse usuário e senha "{password}"'
)
def step_login_existing_user_wrong_password(
    context,
    password: str,
) -> None:
    context.login_page.login(
        context.login_username,
        password,
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
    username_to_use = (
        unique_username("invalid")
        if username == "inexistente"
        else username
    )

    context.login_page.login(
        username_to_use,
        password,
    )


use_step_matcher("parse")


@when("solicito o logout")
def step_logout(
    context,
) -> None:
    context.login_page.logout()


@when(
    "tento acessar diretamente "
    "a transferência de fundos"
)
def step_open_protected_transfer(
    context,
) -> None:
    context.login_page.open_protected_area(
        "transfer.htm"
    )


@then(
    "devo estar autenticado e "
    "visualizar os serviços da conta"
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


@then(
    "devo retornar à tela de login "
    "sem sessão autenticada"
)
def step_validate_logout(
    context,
) -> None:
    context.login_page.validate_logged_out()


@then(
    "a área protegida deve permanecer "
    "inacessível sem sessão autenticada"
)
def step_validate_protected_area_blocked(
    context,
) -> None:
    context.login_page.validate_protected_area_blocked()
