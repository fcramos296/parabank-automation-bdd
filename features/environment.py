import allure
from playwright.sync_api import sync_playwright
from config.settings import settings
from services.parabank_api_client import ParabankApiClient

def before_all(context):
    # Lê o parâmetro -D headless=... passado via terminal/script; se não houver, usa o .env
    headless_arg = context.config.userdata.get("headless")
    if headless_arg is not None:
        is_headless = headless_arg.lower() == "true"
    else:
        is_headless = settings.HEADLESS

    context.playwright = sync_playwright().start()
    browser_type = getattr(context.playwright, settings.BROWSER)

    # Adiciona slow_mo quando em modo visual para permitir acompanhar as ações na tela
    context.browser = browser_type.launch(
        headless=is_headless,
        slow_mo=300 if not is_headless else 0
    )
    context.api_client = ParabankApiClient()

    # Garante o modo JDBC na inicialização
    admin_page = context.browser.new_page()
    try:
        admin_page.goto(f"{settings.BASE_URL}/admin.htm", timeout=15000)
        admin_page.wait_for_load_state("domcontentloaded")
        jdbc_radio = admin_page.locator("input[value='jdbc']")
        if jdbc_radio.is_visible():
            jdbc_radio.check()
            admin_page.locator("input[value='Submit']").click()
            admin_page.wait_for_load_state("domcontentloaded")
    except Exception as e:
        print(f"Aviso ao inicializar modo JDBC: {e}")
    finally:
        admin_page.close()

def before_scenario(context, scenario):
    context.browser_context = context.browser.new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True
    )
    context.page = context.browser_context.new_page()

def after_step(context, step):
    if step.status == "failed" and hasattr(context, "page"):
        try:
            screenshot = context.page.screenshot(full_page=True)
            allure.attach(
                screenshot,
                name=f"failure_{step.name}",
                attachment_type=allure.attachment_type.PNG
            )
        except Exception:
            pass

def after_scenario(context, scenario):
    if hasattr(context, "page"):
        context.page.close()
    if hasattr(context, "browser_context"):
        context.browser_context.close()

def after_all(context):
    if hasattr(context, "browser"):
        context.browser.close()
    if hasattr(context, "playwright"):
        context.playwright.stop()