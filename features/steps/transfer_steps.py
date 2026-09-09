import time
from behave import given, when, then
from pages.login_page import LoginPage
from pages.transfer_page import TransferPage

@given("que estou autenticado no sistema com usuário provisionado via API")
def step_auth_via_seeded_user(context):
    unique_id = int(time.time())
    username = f"transf_{unique_id}"
    password = "Password123!"
    
    payload = {
        "customer.firstName": "Transfer",
        "customer.lastName": "User",
        "customer.address.street": "Bank St",
        "customer.address.city": "Financial City",
        "customer.address.state": "SP",
        "customer.address.zipCode": "11111",
        "customer.phoneNumber": "99998888",
        "customer.ssn": f"{unique_id}"[:9],
        "customer.username": username,
        "customer.password": password,
        "repeatedPassword": password
    }
    context.api_client.register_user(payload)

    login_page = LoginPage(context.page)
    login_page.open()
    login_page.login(username, password)
    login_page.validate_login_success()

@given("navego para a tela de transferência de fundos")
def step_navigate_to_transfer(context):
    context.transfer_page = TransferPage(context.page)
    context.transfer_page.open()

@when('realizo a transferência da quantia de "{amount}" entre as contas')
def step_transfer_funds(context, amount):
    context.transferred_amount = amount
    from_acc, to_acc = context.transfer_page.transfer(amount, from_account_idx=0, to_account_idx=0)
    context.from_account = from_acc
    context.to_account = to_acc

@then('a transferência deve ser concluída exibindo o valor "{amount}" e as contas envolvidas')
def step_assert_transfer_success(context, amount):
    context.transfer_page.validate_transfer_success(
        expected_amount=amount,
        from_acc=context.from_account,
        to_acc=context.to_account
    )

@when('realizo a tentativa de transferência com valor "{amount}"')
def step_attempt_invalid_transfer(context, amount):
    context.transfer_page.transfer(amount, from_account_idx=0, to_account_idx=0)

@then("o sistema deve impedir a operação apresentando indicativo de erro")
def step_assert_transfer_error(context):
    context.transfer_page.validate_transfer_error()