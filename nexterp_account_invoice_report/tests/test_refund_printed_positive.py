# Copyright 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Printing a credit note with the amounts as the customer reads them.

Odoo keeps a credit note positive and tells them apart by the document type;
Romanian practice prints them negative. The setting flips the printed figures
only -- what is booked is untouched.
"""

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestRefundPrintedNegative(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.tax = cls.company_data["default_tax_sale"]

    def _move(self, move_type="out_refund"):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-03-15",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "quantity": 2,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, self.tax.ids)],
                        },
                    )
                ],
            }
        )

    def test_by_default_a_credit_note_prints_positive(self):
        """That is Odoo's way, and it stays the default."""
        self.assertGreater(self._move().tax_totals["total_amount_currency"], 0)

    def test_with_the_setting_on_the_totals_print_negative(self):
        self.company.print_show_refunds = True
        totals = self._move().tax_totals
        self.assertLess(totals["total_amount_currency"], 0)
        self.assertLess(totals["base_amount_currency"], 0)
        self.assertLess(totals["tax_amount_currency"], 0)

    def test_the_tax_lines_under_the_total_turn_too(self):
        self.company.print_show_refunds = True
        for subtotal in self._move().tax_totals["subtotals"]:
            self.assertLess(subtotal["base_amount_currency"], 0)
            for group in subtotal["tax_groups"]:
                self.assertLess(group["tax_amount_currency"], 0)
                self.assertLess(group["base_amount_currency"], 0)

    def test_an_ordinary_invoice_is_left_alone(self):
        self.company.print_show_refunds = True
        self.assertGreater(
            self._move("out_invoice").tax_totals["total_amount_currency"], 0
        )

    def test_a_supplier_credit_note_turns_as_well(self):
        self.company.print_show_refunds = True
        self.assertLess(self._move("in_refund").tax_totals["total_amount_currency"], 0)

    def test_what_is_booked_does_not_move(self):
        """Only the printed figures turn; the accounts keep Odoo's signs."""
        self.company.print_show_refunds = True
        refund = self._move()
        refund.action_post()
        self.assertGreater(refund.amount_total, 0)

    def test_a_unit_can_be_given_its_own_printed_precision(self):
        unit = self.env.ref("uom.product_uom_unit")
        unit.report_precision = 3
        self.assertEqual(unit.report_precision, 3)

    def test_the_settings_follow_the_company(self):
        for field in (
            "print_show_refunds",
            "print_invoice_tax_value",
            "print_invoice_total_value",
        ):
            self.assertFalse(self.company[field], field)
            self.company[field] = True
            self.assertTrue(self.company[field], field)
