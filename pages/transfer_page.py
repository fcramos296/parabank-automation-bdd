from playwright.sync_api import (
    Page,
    expect,
)

from pages.base_page import BasePage


class TransferPage(BasePage):
    def __init__(
        self,
        page: Page,
    ) -> None:
        super().__init__(page)

        self.transfer_funds_link = (
            page.get_by_role(
                "link",
                name="Transfer Funds",
            )
        )

        self.amount_input = page.locator(
            "#amount"
        )

        self.from_account_select = (
            page.locator(
                "#fromAccountId"
            )
        )

        self.to_account_select = (
            page.locator(
                "#toAccountId"
            )
        )

        self.transfer_button = (
            page.get_by_role(
                "button",
                name="Transfer",
            )
        )

        self.transfer_complete_title = (
            page.get_by_role(
                "heading",
                name="Transfer Complete!",
            )
        )

        self.transfer_amount_result = (
            page.locator(
                "#amountResult"
            )
        )

        self.from_account_result = (
            page.locator(
                "#fromAccountIdResult"
            )
        )

        self.to_account_result = (
            page.locator(
                "#toAccountIdResult"
            )
        )

        self.error_panel = page.locator(
            "#showError"
        )

        self.error_title = (
            self.error_panel.locator(
                "h1.title"
            )
        )

        self.error_message = (
            self.error_panel.locator(
                "p.error"
            )
        )

    def open(self) -> None:
        self.transfer_funds_link.click()

        expect(
            self.amount_input
        ).to_be_visible()

        expect(
            self.from_account_select
            .locator("option")
            .nth(1)
        ).to_be_attached()

        expect(
            self.to_account_select
            .locator("option")
            .nth(1)
        ).to_be_attached()

    def transfer(
        self,
        amount: str,
        from_account_id: int,
        to_account_id: int,
    ) -> None:
        self.amount_input.fill(amount)

        self.from_account_select.select_option(
            str(from_account_id)
        )

        self.to_account_select.select_option(
            str(to_account_id)
        )

        self.transfer_button.click()

    def validate_transfer_success(
        self,
        expected_amount: str,
        from_account_id: int,
        to_account_id: int,
    ) -> None:
        expect(
            self.transfer_complete_title
        ).to_be_visible()

        expect(
            self.transfer_amount_result
        ).to_have_text(
            f"${expected_amount}"
        )

        expect(
            self.from_account_result
        ).to_have_text(
            str(from_account_id)
        )

        expect(
            self.to_account_result
        ).to_have_text(
            str(to_account_id)
        )

    def validate_transfer_error(
        self,
        expected_message: str,
    ) -> None:
        expect(
            self.error_panel
        ).to_be_visible()

        expect(
            self.error_title
        ).to_have_text("Error!")

        expect(
            self.error_message
        ).to_contain_text(
            expected_message
        )

        expect(
            self.transfer_complete_title
        ).not_to_be_visible()