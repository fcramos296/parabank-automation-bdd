import time
from behave import given, when, then
from pages.register_page import RegisterPage

@given("que estou na página de registro")
def step_open_registration(context):
    context.register_page = RegisterPage(context.page)
    context.register_page.open()

@when("preencho o formulário de cadastro com dados dinâmicos válidos")
def step_fill_valid_registration(context):
    unique_id = int(time.time() * 1000)
    context.current_username = f"user_{unique_id}"
    context.current_password = f"Pass@{unique_id}"
    
    data = {
        "first_name": "Test",
        "last_name": "Automation",
        "address": "Av. Paulista 1000",
        "city": "Sao Paulo",
        "state": "SP",
        "zip_code": "01310-100",
        "phone": "11999999999",
        "ssn": f"{unique_id}"[:9],
        "username": context.current_username,
        "password": context.current_password,
        "confirm_password": context.current_password
    }
    context.register_page.fill_registration_form(data)

@when('preencho o formulário informando a senha "{password}" e confirmação "{confirm}"')
def step_fill_mismatched_password(context, password, confirm):
    unique_id = int(time.time() * 1000)
    data = {
        "first_name": "Mismatch",
        "last_name": "User",
        "address": "Street 1",
        "city": "City",
        "state": "ST",
        "zip_code": "12345",
        "phone": "11888888888",
        "ssn": "123456789",
        "username": f"user_err_{unique_id}",
        "password": password,
        "confirm_password": confirm
    }
    context.register_page.fill_registration_form(data)

@given('que um usuário "{username}" foi previamente provisionado via API')
def step_seed_user_api(context, username):
    unique_id = int(time.time() * 1000)
    context.existing_user = f"{username}_{unique_id}"
    payload = {
        "customer.firstName": "PreLoaded",
        "customer.lastName": "Customer",
        "customer.address.street": "API Street",
        "customer.address.city": "API City",
        "customer.address.state": "SP",
        "customer.address.zipCode": "00000",
        "customer.phoneNumber": "00000000",
        "customer.ssn": f"{unique_id}"[:9],
        "customer.username": context.existing_user,
        "customer.password": "Password123!",
        "repeatedPassword": "Password123!"
    }
    context.api_client.register_user(payload)

@when('preencho o formulário de cadastro utilizando o username "{existing_username}"')
def step_fill_with_existing_user(context, existing_username):
    username_to_use = getattr(context, "existing_user", existing_username)
    data = {
        "first_name": "Existing",
        "last_name": "User",
        "address": "Street 2",
        "city": "City",
        "state": "ST",
        "zip_code": "12345",
        "phone": "11777777777",
        "ssn": "987654321",
        "username": username_to_use,
        "password": "Password123!",
        "confirm_password": "Password123!"
    }
    context.register_page.fill_registration_form(data)

@when("submeto o formulário de registro")
def step_submit_registration(context):
    context.register_page.submit()

@then("devo visualizar a mensagem de boas-vindas do usuário registrado")
def step_assert_registration_success(context):
    context.register_page.validate_success(context.current_username)

@then('devo visualizar o erro de validação de confirmação de senha "{message}"')
def step_assert_password_error(context, message):
    context.register_page.validate_password_mismatch_error(message)

@then('devo visualizar a mensagem de erro "{message}"')
def step_assert_username_error(context, message):
    context.register_page.validate_username_error(message)