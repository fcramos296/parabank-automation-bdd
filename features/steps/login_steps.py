from behave import given, then, when

from pages.login_page import LoginPage
from pages.transfer_page import TransferPage
from utils.gherkin_values import normalize_example_value
from utils.test_data import build_customer, unique_username


@given("que estou na tela de login")
def step_open_login(context) -> None:
    context.login_page = LoginPage(context.page)
    context.login_page.open()


@given("que existe um usuário exclusivo cadastrado para autenticação")
def step_seed_exclusive_login_user(context) -> None:
    context.login_customer = build_customer("login")
    context.api_client.register_user(context.login_customer.registration_payload())
    context.login_username = context.login_customer.username
    context.login_password = context.login_customer.password


@when("informo as credenciais válidas desse usuário")
def step_login_with_valid_credentials(context) -> None:
    context.login_page.login(
        context.login_username,
        context.login_password,
    )


@when("tento novamente com as credenciais válidas desse usuário")
def step_retry_with_valid_credentials(context) -> None:
    context.login_page.login(
        context.login_username,
        context.login_password,
    )


@when('realizo login com esse usuário e senha "{password}"')
def step_login_existing_user_wrong_password(context, password: str) -> None:
    context.login_page.login(context.login_username, password)


@when('realizo login com usuário "{username}" e senha "{password}"')
def step_login_with_params(context, username: str, password: str) -> None:
    normalized_username = normalize_example_value(username)
    normalized_password = normalize_example_value(password)

    username_to_use = (
        unique_username("invalid")
        if normalized_username == "inexistente"
        else normalized_username
    )

    context.login_page.login(username_to_use, normalized_password)


@when("recarrego a página autenticada")
def step_reload_authenticated_page(context) -> None:
    context.login_page.reload_authenticated_page()


@when("solicito o logout")
def step_logout(context) -> None:
    context.login_page.logout()


@when("tento acessar diretamente a transferência de fundos")
def step_open_protected_transfer(context) -> None:
    context.transfer_page = TransferPage(context.page)
    context.transfer_page.open_direct()


@then("devo estar autenticado e visualizar os serviços da conta")
def step_validate_login_success(context) -> None:
    context.login_page.validate_login_success()


@then('devo visualizar a mensagem de erro de autenticação "{error_message}"')
def step_validate_login_failure(context, error_message: str) -> None:
    context.login_page.validate_login_failure(error_message)


@then("devo retornar à tela de login sem sessão autenticada")
def step_validate_logout(context) -> None:
    context.login_page.validate_logged_out()


@then("a área protegida deve permanecer inacessível sem sessão autenticada")
def step_validate_protected_area_blocked(context) -> None:
    context.login_page.validate_no_authenticated_session()
    context.transfer_page.validate_unavailable_without_session()
