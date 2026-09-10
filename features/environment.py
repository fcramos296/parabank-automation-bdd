import platform
import time
from pathlib import Path

import allure
from playwright.sync_api import (
    ConsoleMessage,
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

ALLURE_RESULTS_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "reports"
    / "allure-results"
)


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


def _handle_resource(
    route: Route,
) -> None:
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


def _write_allure_environment(
    context,
) -> None:
    ALLURE_RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    execution_mode = (
        "headless"
        if context.headless
        else "headed"
    )

    properties = [
        "sut=ParaBank",
        "environment=Local Docker",
        f"base_url={settings.BASE_URL}",
        f"browser={context.browser_name}",
        f"execution_mode={execution_mode}",
        f"python={platform.python_version()}",
        f"os={platform.system()} {platform.release()}",
        "framework=Playwright + Behave",
    ]

    (
        ALLURE_RESULTS_DIR
        / "environment.properties"
    ).write_text(
        "\n".join(properties) + "\n",
        encoding="utf-8",
    )


def _record_console_message(
    context,
    message: ConsoleMessage,
) -> None:
    if message.type != "error":
        return

    context.browser_console_errors.append(
        message.text
    )


def _apply_allure_metadata(
    context,
    scenario,
) -> None:
    feature_name = getattr(
        context.feature,
        "name",
        "ParaBank",
    )

    feature_tags = {
        str(tag).lower()
        for tag in getattr(
            context.feature,
            "tags",
            [],
        )
    }

    scenario_tags = {
        str(tag).lower()
        for tag in getattr(
            scenario,
            "tags",
            [],
        )
    }

    tags = feature_tags | scenario_tags

    allure.dynamic.label(
        "epic",
        "ParaBank",
    )

    allure.dynamic.label(
        "feature",
        feature_name,
    )

    allure.dynamic.label(
        "browser",
        context.browser_name,
    )

    allure.dynamic.label(
        "environment",
        "local-docker",
    )

    allure.dynamic.label(
        "layer",
        "e2e",
    )

    allure.dynamic.label(
        "severity",
        (
            "critical"
            if "smoke" in tags
            else "normal"
        ),
    )


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

    _write_allure_environment(
        context
    )

    context.playwright = (
        sync_playwright().start()
    )

    browser_type = getattr(
        context.playwright,
        context.browser_name,
    )

    print(
        "[browser] Playwright will access "
        f"ParaBank directly at {settings.BASE_URL}."
    )

    if settings.BLOCK_NONESSENTIAL_RESOURCES:
        print(
            "[browser] Non-essential resources are blocked."
        )

    context.browser = browser_type.launch(
        headless=context.headless,
    )

    context.api_client = (
        ParabankApiClient()
    )


def before_scenario(
    context,
    scenario,
) -> None:
    _apply_allure_metadata(
        context,
        scenario,
    )

    context.browser_console_errors = []

    context.browser_context = (
        context.browser.new_context(
            viewport={
                "width": 1280,
                "height": 720,
            },
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

    context.page.on(
        "console",
        lambda message: _record_console_message(
            context,
            message,
        ),
    )

    context.page.set_default_navigation_timeout(
        settings.PW_NAVIGATION_TIMEOUT_MS
    )


def after_step(
    context,
    step,
) -> None:
    if step.status.name != "failed":
        return

    page = getattr(
        context,
        "page",
        None,
    )

    if page is None:
        return

    try:
        allure.attach(
            page.url,
            name="Current URL",
            attachment_type=(
                allure.attachment_type.TEXT
            ),
        )

        console_errors = getattr(
            context,
            "browser_console_errors",
            [],
        )

        if console_errors:
            allure.attach(
                "\n".join(console_errors),
                name="Browser console errors",
                attachment_type=(
                    allure.attachment_type.TEXT
                ),
            )

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
            f"failure evidence: {exc}"
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
        context.browser_context = None

    delay = settings.UI_SCENARIO_DELAY_SECONDS

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
