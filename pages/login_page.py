from playwright.sync_api import (
    Page,
    expect,
)

from pages.base_page import BasePage


class LoginPage(BasePage):
    def __init__(
        self,
        page: Page,
    ) -> None:
        super().__init__(page)

        self.username_input = page.locator(
            "input[name='username']"
        )

        self.password_input = page.locator(
            "input[name='password']"
        )

        self.login_button = page.get_by_role(
            "button",
            name="Log In",
        )

        self.authenticated_panel = page.locator(
            "#leftPanel"
        )

        self.account_services_title = (
            page.get_by_role(
                "heading",
                name="Account Services",
            )
        )

        self.logout_link = (
            page.get_by_role(
                "link",
                name="Log Out",
            )
        )

        self.transfer_amount_input = (
            page.locator(
                "#amount"
            )
        )

        self.transfer_button = (
            page.get_by_role(
                "button",
                name="Transfer",
                exact=True,
            )
        )

    @property
    def visible_error_message(self):
        return self.page.locator(
            "p.error:visible"
        ).first

    def open(self) -> None:
        self.navigate_to(
            "index.htm"
        )

        expect(
            self.username_input
        ).to_be_visible()

        expect(
            self.password_input
        ).to_be_visible()

        expect(
            self.logout_link
        ).not_to_be_visible()

    def login(
        self,
        username: str,
        password: str,
    ) -> None:
        self.username_input.fill(
            username
        )

        self.password_input.fill(
            password
        )

        self.login_button.click()

    def reload_authenticated_page(self) -> None:
        expect(
            self.logout_link
        ).to_be_visible()

        self.page.reload(
            wait_until="domcontentloaded"
        )

    def logout(self) -> None:
        expect(
            self.logout_link
        ).to_be_visible()

        self.logout_link.click()

        expect(
            self.username_input
        ).to_be_visible()

        expect(
            self.password_input
        ).to_be_visible()

    def open_protected_area(
        self,
        path: str,
    ) -> None:
        self.navigate_to(
            path
        )

    def validate_login_success(
        self,
    ) -> None:
        expect(
            self.authenticated_panel
        ).to_contain_text(
            "Welcome"
        )

        expect(
            self.account_services_title
        ).to_be_visible()

        expect(
            self.logout_link
        ).to_be_visible()

    def validate_login_failure(
        self,
        expected_message: str,
    ) -> None:
        expect(
            self.visible_error_message
        ).to_be_visible()

        expect(
            self.visible_error_message
        ).to_contain_text(
            expected_message
        )

        expect(
            self.username_input
        ).to_be_visible()

        expect(
            self.logout_link
        ).not_to_be_visible()

    def validate_logged_out(
        self,
    ) -> None:
        expect(
            self.username_input
        ).to_be_visible()

        expect(
            self.password_input
        ).to_be_visible()

        expect(
            self.logout_link
        ).not_to_be_visible()

        expect(
            self.account_services_title
        ).not_to_be_visible()

    def validate_protected_area_blocked(
        self,
    ) -> None:
        """
        Confirms that a protected function cannot be used
        after logout, without coupling the test to the exact
        error page/message returned by the current ParaBank
        version for a direct unauthenticated request.
        """

        expect(
            self.logout_link
        ).not_to_be_visible()

        expect(
            self.account_services_title
        ).not_to_be_visible()

        expect(
            self.transfer_amount_input
        ).not_to_be_visible()

        expect(
            self.transfer_button
        ).not_to_be_visible()
