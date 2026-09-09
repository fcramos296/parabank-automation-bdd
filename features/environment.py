import secrets
import time

import allure
from playwright.sync_api import (
    Route,
    sync_playwright,
)

from config.settings import settings
from services.parabank_api_client import (
    ParabankApiClient,
)


BLOCKED_RESOURCE_TYPES = {
    "image",
    "media",
    "font",
}


def _userdata_bool(
    context,
    name: str,
    default: bool,
) -> bool:
    value = context.config.userdata.get(
        name
    )

    if value is None:
        return default

    return str(value).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _build_browser_proxy() -> dict | None:
    """
    Optional browser proxy.

    Kept available for environments/plans where
    Scrape.do Proxy Mode has enough concurrency,
    but disabled by default for this project.
    """

    if (
        settings.BROWSER_TRANSPORT
        != "proxy"
    ):
        return None

    token = settings.scrape_do_token

    if not token:
        raise RuntimeError(
            "BROWSER_TRANSPORT=proxy "
            "requires SCRAPE_DO_TOKEN."
        )

    session_id = secrets.randbelow(
        1_000_001
    )

    params = (
        settings
        .SCRAPE_DO_BROWSER_PROXY_PARAMS
        .strip()
        .strip("&")
    )

    if params:
        password = (
            f"{params}"
            f"&sessionId={session_id}"
        )
    else:
        password = (
            f"sessionId={session_id}"
        )

    return {
        "server": settings.SCRAPE_DO_PROXY_URL,
        "username": token,
        "password": password,
    }


def _handle_resource(
    route: Route,
) -> None:
    """
    Avoid downloading resources that do not
    contribute to functional assertions.

    Scripts and stylesheets remain enabled because
    they can affect application behavior and
    Playwright visibility calculations.
    """

    resource_type = (
        route.request.resource_type
    )

    if (
        settings.BLOCK_NONESSENTIAL_RESOURCES
        and resource_type
        in BLOCKED_RESOURCE_TYPES
    ):
        route.abort()
        return

    route.continue_()


def before_all(context) -> None:
    context.headless = _userdata_bool(
        context,
        "headless",
        settings.HEADLESS,
    )

    context.browser_name = (
        context.config.userdata.get(
            "browser",
            settings.BROWSER,
        )
    )

    supported_browsers = {
        "chromium",
        "firefox",
        "webkit",
    }

    if (
        context.browser_name
        not in supported_browsers
    ):
        raise ValueError(
            "Unsupported browser: "
            f"{context.browser_name}"
        )

    context.playwright = (
        sync_playwright().start()
    )

    browser_type = getattr(
        context.playwright,
        context.browser_name,
    )

    launch_options = {
        "headless": context.headless,
    }

    browser_proxy = (
        _build_browser_proxy()
    )

    if browser_proxy:
        launch_options["proxy"] = (
            browser_proxy
        )

        print(
            "[browser] Playwright traffic "
            "will use Scrape.do Proxy Mode."
        )

    else:
        print(
            "[browser] Playwright will access "
            "ParaBank directly."
        )

        if (
            settings
            .BLOCK_NONESSENTIAL_RESOURCES
        ):
            print(
                "[browser] Non-essential "
                "resources are blocked."
            )

    context.browser = (
        browser_type.launch(
            **launch_options
        )
    )

    context.api_client = (
        ParabankApiClient()
    )


def before_scenario(
    context,
    scenario,
) -> None:
    use_proxy = (
        settings.BROWSER_TRANSPORT
        == "proxy"
    )

    context.browser_context = (
        context.browser.new_context(
            viewport={
                "width": 1280,
                "height": 720,
            },
            ignore_https_errors=use_proxy,
        )
    )

    context.browser_context.set_default_timeout(
        settings.PW_TIMEOUT_MS
    )

    context.browser_context.route(
        "**/*",
        _handle_resource,
    )

    context.page = (
        context.browser_context.new_page()
    )

    context.page.set_default_navigation_timeout(
        settings.PW_NAVIGATION_TIMEOUT_MS
    )


def after_step(
    context,
    step,
) -> None:
    if (
        step.status.name
        != "failed"
    ):
        return

    page = getattr(
        context,
        "page",
        None,
    )

    if page is None:
        return

    try:
        screenshot = page.screenshot(
            full_page=True
        )

        allure.attach(
            screenshot,
            name=f"failure-{step.name}",
            attachment_type=(
                allure.attachment_type.PNG
            ),
        )

    except Exception as exc:
        print(
            "[diagnostic] Unable to attach "
            f"failure screenshot: {exc}"
        )


def after_scenario(
    context,
    scenario,
) -> None:
    browser_context = getattr(
        context,
        "browser_context",
        None,
    )

    if browser_context:
        browser_context.close()

    delay = (
        settings.UI_SCENARIO_DELAY_SECONDS
    )

    if delay > 0:
        time.sleep(delay)


def after_all(context) -> None:
    browser = getattr(
        context,
        "browser",
        None,
    )

    if browser:
        browser.close()

    playwright = getattr(
        context,
        "playwright",
        None,
    )

    if playwright:
        playwright.stop()