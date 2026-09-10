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

        self.error_message = page.locator(
            "p.error"
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

    @property
    def visible_error_message(self):
        return self.page.locator(
            "p.error:visible"
        ).first

    def open(self) -> None:
        """
        Opens the login page from an explicitly
        unauthenticated server-side session.

        ParaBank's public instance is shared and has
        demonstrated inconsistent session state between
        requests. Visiting logout.htm first invalidates any
        session that may already exist for this browser
        context and redirects back to index.htm.
        """

        self.navigate_to(
            "logout.htm"
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
        """
        Validates authentication without depending on
        account-table contents or a specific balance.
        """

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

    def validate_unauthenticated_with_error(
        self,
    ) -> None:
        """
        Confirms that invalid credentials leave the user
        unauthenticated and that the application presents
        a visible error response.

        Hidden template errors are intentionally ignored.
        """

        expect(
            self.visible_error_message
        ).to_be_visible()

        expect(
            self.visible_error_message
        ).not_to_have_text("")

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

    def validate_authentication_required(
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
            self.password_input
        ).to_be_visible()

        expect(
            self.logout_link
        ).not_to_be_visible()
