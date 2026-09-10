import time

import allure
from playwright.sync_api import Route, sync_playwright

from config.settings import settings
from services.parabank_api_client import ParabankApiClient


DEFAULT_HEADLESS = True
DEFAULT_BROWSER = "chromium"
SUPPORTED_BROWSERS = {"chromium", "firefox", "webkit"}
BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}


def _userdata_bool(context, name: str, default: bool) -> bool:
    value = context.config.userdata.get(name)
    if value is None:
        return default

    return str(value).lower() in {"1", "true", "yes", "on"}


def _handle_resource(route: Route) -> None:
    resource_type = route.request.resource_type

    if (
        settings.BLOCK_NONESSENTIAL_RESOURCES
        and resource_type in BLOCKED_RESOURCE_TYPES
    ):
        route.abort()
        return

    route.continue_()


def before_all(context) -> None:
    context.headless = _userdata_bool(context, "headless", DEFAULT_HEADLESS)
    context.browser_name = context.config.userdata.get("browser", DEFAULT_BROWSER)

    if context.browser_name not in SUPPORTED_BROWSERS:
        raise ValueError(f"Unsupported browser: {context.browser_name}")

    context.playwright = sync_playwright().start()
    browser_type = getattr(context.playwright, context.browser_name)

    print(
        "[browser] Playwright will access "
        f"ParaBank directly at {settings.BASE_URL}."
    )

    if settings.BLOCK_NONESSENTIAL_RESOURCES:
        print("[browser] Non-essential resources are blocked.")

    context.browser = browser_type.launch(headless=context.headless)
    context.api_client = ParabankApiClient()


def before_scenario(context, scenario) -> None:
    context.browser_context = context.browser.new_context(
        viewport={"width": 1280, "height": 720}
    )
    context.browser_context.set_default_timeout(settings.PW_TIMEOUT_MS)
    context.browser_context.route("**/*", _handle_resource)

    context.page = context.browser_context.new_page()
    context.page.set_default_navigation_timeout(settings.PW_NAVIGATION_TIMEOUT_MS)


def after_step(context, step) -> None:
    if step.status.name != "failed":
        return

    page = getattr(context, "page", None)
    if page is None:
        return

    try:
        screenshot = page.screenshot(full_page=True)
        allure.attach(
            screenshot,
            name=f"failure-{step.name}",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as exc:
        print(f"[diagnostic] Unable to attach failure screenshot: {exc}")


def after_scenario(context, scenario) -> None:
    browser_context = getattr(context, "browser_context", None)
    if browser_context:
        browser_context.close()
        context.browser_context = None

    delay = settings.UI_SCENARIO_DELAY_SECONDS
    if delay > 0:
        time.sleep(delay)


def after_all(context) -> None:
    browser = getattr(context, "browser", None)
    if browser:
        browser.close()

    playwright = getattr(context, "playwright", None)
    if playwright:
        playwright.stop()
