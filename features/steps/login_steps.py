import time
from behave import given, when, then, use_step_matcher
from pages.login_page import LoginPage

@given("que estou na tela de login")
def step_open_login(context):
    context.login_page = LoginPage(context.page)
    context.login_page.open()

@given("que existe um usuário registrado via API com credenciais válidas")
def step_create_valid_user_via_api(context):
    unique_id = int(time.time())
    # Mantém o tamanho total em 12 caracteres (limite máximo do Parabank é 20)
    context.seeded_username = f"u_{unique_id}"
    context.seeded_password = "Password123!"
    
    payload = {
        "customer.firstName": "API",
        "customer.lastName": "Tester",
        "customer.address.street": "Rue 10",
        "customer.address.city": "City",
        "customer.address.state": "SP",
        "customer.address.zipCode": "12345",
        "customer.phoneNumber": "12345678",
        "customer.ssn": f"{unique_id}"[:9],
        "customer.username": context.seeded_username,
        "customer.password": context.seeded_password,
        "repeatedPassword": context.seeded_password
    }
    response = context.api_client.register_user(payload)
    assert response.status_code in [200, 302], f"Falha ao registrar usuário via API: {response.text}"

@when("informo o usuário e senha cadastrados")
def step_login_with_seeded_credentials(context):
    context.login_page.login(context.seeded_username, context.seeded_password)

use_step_matcher("re")

@when(r'realizo login com usuário "(?P<username>.*)" e senha "(?P<password>.*)"')
def step_login_with_params(context, username, password):
    user_to_login = username
    if username and username != "user_sem_pass":
        user_to_login = f"inv_{int(time.time())}"
    
    context.login_page.login(user_to_login, password)

use_step_matcher("parse")

@then("sou direcionado para a tela de visão geral da conta")
def step_validate_login_success(context):
    context.login_page.validate_login_success()

@then('devo visualizar a mensagem de erro de autenticação "{error_message}"')
def step_validate_login_failure(context, error_message):
    context.login_page.validate_login_failure(error_message)