from playwright.sync_api import Page

from config.settings import settings


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def navigate_to(self, path: str = "") -> None:
        url = f"{settings.BASE_URL.rstrip('/')}/{path.lstrip('/')}"
        self.page.goto(url, wait_until="domcontentloaded")
