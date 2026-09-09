from playwright.sync_api import Page, Locator, expect

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def navigate_to(self, path: str = "") -> None:
        from config.settings import settings
        self.page.goto(f"{settings.BASE_URL}/{path}".strip("/"))

    def get_element(self, selector: str) -> Locator:
        return self.page.locator(selector)

    def wait_for_visible(self, locator: Locator) -> None:
        expect(locator).to_be_visible()