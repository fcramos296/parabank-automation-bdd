from playwright.sync_api import Page, expect
from pages.base_page import BasePage

class RegisterPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.first_name_input = page.locator("input[id='customer.firstName']")
        self.last_name_input = page.locator("input[id='customer.lastName']")
        self.address_input = page.locator("input[id='customer.address.street']")
        self.city_input = page.locator("input[id='customer.address.city']")
        self.state_input = page.locator("input[id='customer.address.state']")
        self.zip_code_input = page.locator("input[id='customer.address.zipCode']")
        self.phone_input = page.locator("input[id='customer.phoneNumber']")
        self.ssn_input = page.locator("input[id='customer.ssn']")
        self.username_input = page.locator("input[id='customer.username']")
        self.password_input = page.locator("input[id='customer.password']")
        self.confirm_password_input = page.locator("input[id='repeatedPassword']")
        self.register_button = page.locator("input[value='Register']")
        self.success_title = page.locator("h1.title")
        self.success_message = page.locator("div#rightPanel p")
        self.username_error = page.locator("span[id='customer.username.errors']")
        self.confirm_password_error = page.locator("span[id='repeatedPassword.errors']")

    def open(self) -> None:
        self.navigate_to("register.htm")

    def fill_registration_form(self, data: dict) -> None:
        if "first_name" in data: self.first_name_input.fill(data["first_name"])
        if "last_name" in data: self.last_name_input.fill(data["last_name"])
        if "address" in data: self.address_input.fill(data["address"])
        if "city" in data: self.city_input.fill(data["city"])
        if "state" in data: self.state_input.fill(data["state"])
        if "zip_code" in data: self.zip_code_input.fill(data["zip_code"])
        if "phone" in data: self.phone_input.fill(data["phone"])
        if "ssn" in data: self.ssn_input.fill(data["ssn"])
        if "username" in data: self.username_input.fill(data["username"])
        if "password" in data: self.password_input.fill(data["password"])
        if "confirm_password" in data: self.confirm_password_input.fill(data["confirm_password"])

    def submit(self) -> None:
        self.register_button.click()

    def validate_success(self, username: str) -> None:
        expect(self.success_title).to_have_text(f"Welcome {username}")
        expect(self.success_message).to_contain_text("Your account was created successfully.")

    def validate_username_error(self, message: str) -> None:
        expect(self.username_error).to_be_visible()
        expect(self.username_error).to_contain_text(message)

    def validate_password_mismatch_error(self, message: str) -> None:
        expect(self.confirm_password_error).to_be_visible()
        expect(self.confirm_password_error).to_contain_text(message)