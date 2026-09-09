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

    def validate_login_success(
        self,
    ) -> None:
        """
        Valida autenticação sem depender do carregamento
        do serviço Accounts Overview.
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
            self.error_message.first
        ).to_be_visible()

        expect(
            self.error_message.first
        ).to_contain_text(
            expected_message
        )

    def validate_unauthenticated_with_error(
        self,
    ) -> None:
        """
        Valida que a tentativa de autenticação inválida
        produziu uma resposta de erro.

        O ambiente público do ParaBank pode renderizar
        elementos inconsistentes do menu lateral, inclusive
        o link Log Out, mesmo após uma tentativa inválida.
        Por isso o estado negativo é validado pelo retorno
        explícito de erro da aplicação.
        """

        expect(
            self.error_message.first
        ).to_be_visible()

        expect(
            self.error_message.first
        ).not_to_have_text("")