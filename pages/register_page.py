from playwright.sync_api import (
    Page,
    expect,
)

from pages.base_page import BasePage


class RegisterPage(BasePage):
    def __init__(
        self,
        page: Page,
    ) -> None:
        super().__init__(page)

        self.first_name_input = page.locator(
            "input[id='customer.firstName']"
        )

        self.last_name_input = page.locator(
            "input[id='customer.lastName']"
        )

        self.address_input = page.locator(
            "input[id='customer.address.street']"
        )

        self.city_input = page.locator(
            "input[id='customer.address.city']"
        )

        self.state_input = page.locator(
            "input[id='customer.address.state']"
        )

        self.zip_code_input = page.locator(
            "input[id='customer.address.zipCode']"
        )

        self.phone_input = page.locator(
            "input[id='customer.phoneNumber']"
        )

        self.ssn_input = page.locator(
            "input[id='customer.ssn']"
        )

        self.username_input = page.locator(
            "input[id='customer.username']"
        )

        self.password_input = page.locator(
            "input[id='customer.password']"
        )

        self.confirm_password_input = page.locator(
            "input[id='repeatedPassword']"
        )

        self.register_button = (
            page.get_by_role(
                "button",
                name="Register",
            )
        )

        self.success_title = page.locator(
            "h1.title"
        )

        self.success_message = page.locator(
            "div#rightPanel p"
        )

        self.username_error = page.locator(
            "span[id='customer.username.errors']"
        )

        self.confirm_password_error = (
            page.locator(
                "span[id='repeatedPassword.errors']"
            )
        )

    def open(self) -> None:
        self.navigate_to("register.htm")

        expect(
            self.first_name_input
        ).to_be_visible()

    def fill_registration_form(
        self,
        data: dict[str, str],
    ) -> None:
        fields = {
            "first_name": self.first_name_input,
            "last_name": self.last_name_input,
            "address": self.address_input,
            "city": self.city_input,
            "state": self.state_input,
            "zip_code": self.zip_code_input,
            "phone": self.phone_input,
            "ssn": self.ssn_input,
            "username": self.username_input,
            "password": self.password_input,
            "confirm_password": (
                self.confirm_password_input
            ),
        }

        for field_name, locator in fields.items():
            if field_name in data:
                locator.fill(
                    data[field_name]
                )

    def submit(self) -> None:
        self.register_button.click()

    def validate_success(
        self,
        username: str,
    ) -> None:
        expect(
            self.success_title
        ).to_have_text(
            f"Welcome {username}"
        )

        expect(
            self.success_message
        ).to_contain_text(
            "Your account was created successfully."
        )

    def validate_username_error(
        self,
        message: str,
    ) -> None:
        expect(
            self.username_error
        ).to_be_visible()

        expect(
            self.username_error
        ).to_contain_text(message)

    def validate_password_mismatch_error(
        self,
        message: str,
    ) -> None:
        expect(
            self.confirm_password_error
        ).to_be_visible()

        expect(
            self.confirm_password_error
        ).to_contain_text(message)