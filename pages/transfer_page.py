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

    @staticmethod
    def _option_values(select) -> set[int]:
        options = select.locator("option")
        values: set[int] = set()

        for index in range(options.count()):
            value = options.nth(index).get_attribute(
                "value"
            )

            if value is None or not value.strip():
                continue

            values.add(int(value))

        return values

    def validate_account_options(
        self,
        expected_account_ids: set[int],
        forbidden_account_ids: set[int] | None = None,
    ) -> None:
        from_values = self._option_values(
            self.from_account_select
        )

        to_values = self._option_values(
            self.to_account_select
        )

        if from_values != expected_account_ids:
            raise AssertionError(
                "Unexpected source-account options. "
                f"Expected: {sorted(expected_account_ids)}. "
                f"Actual: {sorted(from_values)}."
            )

        if to_values != expected_account_ids:
            raise AssertionError(
                "Unexpected target-account options. "
                f"Expected: {sorted(expected_account_ids)}. "
                f"Actual: {sorted(to_values)}."
            )

        forbidden = forbidden_account_ids or set()

        exposed = (
            from_values | to_values
        ) & forbidden

        if exposed:
            raise AssertionError(
                "Transfer selectors exposed accounts that do "
                "not belong to the authenticated customer: "
                f"{sorted(exposed)}"
            )

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
