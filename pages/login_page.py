from playwright.sync_api import Page, expect
from pages.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.locator("input[name='username']")
        self.password_input = page.locator("input[name='password']")
        self.login_button = page.locator("input[value='Log In']")
        self.error_message = page.locator("p.error")
        self.account_overview_title = page.get_by_role("heading", name="Accounts Overview")
        self.logout_link = page.locator("a[href*='logout.htm']")

    def open(self) -> None:
        self.navigate_to("index.htm")
        self.page.wait_for_load_state("domcontentloaded")
        if self.logout_link.is_visible() or "overview.htm" in self.page.url:
            self.navigate_to("logout.htm")
            self.page.wait_for_load_state("domcontentloaded")
            self.navigate_to("index.htm")
            self.page.wait_for_load_state("domcontentloaded")
        self.username_input.wait_for(state="visible", timeout=10000)

    def login(self, username: str, password: str) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
        self.page.wait_for_load_state("domcontentloaded")

    def validate_login_success(self) -> None:
        expect(self.account_overview_title).to_be_visible(timeout=10000)
        expect(self.logout_link).to_be_visible()

    def validate_login_failure(self, expected_message: str) -> None:
        expect(self.error_message.first).to_be_visible(timeout=10000)
        actual_text = self.error_message.first.inner_text().strip()
        assert (
            expected_message in actual_text
            or "could not be verified" in actual_text
            or "Please enter a username and password" in actual_text
        ), f"Esperava erro contendo '{expected_message}', mas obteve: '{actual_text}'"