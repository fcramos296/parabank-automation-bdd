from playwright.sync_api import Page, expect
from pages.base_page import BasePage

class TransferPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.transfer_funds_link = page.locator("a[href*='transfer.htm']")
        self.amount_input = page.locator("input#amount")
        self.from_account_select = page.locator("select#fromAccountId")
        self.to_account_select = page.locator("select#toAccountId")
        self.transfer_button = page.locator("input[value='Transfer']")
        self.transfer_complete_title = page.get_by_role("heading", name="Transfer Complete!")
        self.transfer_amount_result = page.locator("span#amountResult")
        self.from_account_result = page.locator("span#fromAccountIdResult")
        self.to_account_result = page.locator("span#toAccountIdResult")

    def open(self) -> None:
        self.transfer_funds_link.click()
        self.page.wait_for_load_state("networkidle")

    def transfer(self, amount: str, from_account_idx: int = 0, to_account_idx: int = 0) -> tuple[str, str]:
        self.from_account_select.wait_for(state="visible")
        # Aguarda o Parabank preencher os selects via AJAX
        self.page.wait_for_function("document.querySelectorAll('select#fromAccountId option').length > 0")
        self.amount_input.fill(amount)

        from_options = self.from_account_select.locator("option").all_inner_texts()
        to_options = self.to_account_select.locator("option").all_inner_texts()

        from_acc = from_options[from_account_idx] if from_options else ""
        to_acc = to_options[to_account_idx] if to_options else ""

        self.from_account_select.select_option(value=from_acc)
        self.to_account_select.select_option(value=to_acc)
        self.transfer_button.click()
        return from_acc, to_acc

    def validate_transfer_success(self, expected_amount: str, from_acc: str, to_acc: str) -> None:
        expect(self.transfer_complete_title).to_be_visible()
        expect(self.transfer_amount_result).to_have_text(f"${expected_amount}")
        expect(self.from_account_result).to_have_text(from_acc)
        expect(self.to_account_result).to_have_text(to_acc)

    def validate_transfer_error(self) -> None:
        expect(self.transfer_complete_title).not_to_be_visible()