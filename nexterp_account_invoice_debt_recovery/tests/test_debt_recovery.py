# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""An invoice handed over for debt recovery.

It stops being an ordinary unpaid invoice and shows its own payment state, so
it no longer sits in the dunning lists -- until it is actually paid, when it
goes back to being paid like any other.
"""

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestDebtRecovery(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    def _invoice(self, post=True):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-03-15",
                "invoice_line_ids": [
                    (0, 0, {"product_id": self.product_a.id, "price_unit": 100.0})
                ],
            }
        )
        if post:
            move.action_post()
        return move

    def _pay(self, invoice):
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({})._create_payments()

    # ------------------------------------------------------------------
    # Trecerea in recuperare
    # ------------------------------------------------------------------
    def test_without_the_setting_the_button_does_nothing(self):
        invoice = self._invoice()
        invoice.action_mark_as_debt_recovery()
        self.assertFalse(invoice.debt_recovery)
        self.assertEqual(invoice.payment_state, "not_paid")

    def test_with_the_setting_on_the_invoice_goes_into_recovery(self):
        self.company.account_allow_debt_recovery_invoice = True
        invoice = self._invoice()
        invoice.action_mark_as_debt_recovery()
        self.assertTrue(invoice.debt_recovery)
        self.assertEqual(invoice.payment_state, "debt_recovery")

    def test_the_state_holds_while_the_invoice_stays_unpaid(self):
        """Recomputing the amounts must not put it back among the ordinary
        unpaid invoices."""
        self.company.account_allow_debt_recovery_invoice = True
        invoice = self._invoice()
        invoice.action_mark_as_debt_recovery()
        invoice.invalidate_recordset(["amount_residual"])
        invoice._compute_amount()
        self.assertEqual(invoice.payment_state, "debt_recovery")

    def test_paying_it_closes_the_recovery(self):
        self.company.account_allow_debt_recovery_invoice = True
        invoice = self._invoice()
        invoice.action_mark_as_debt_recovery()
        self._pay(invoice)
        self.assertEqual(invoice.payment_state, "paid")
        self.assertTrue(invoice.debt_recovery_done)

    def test_an_invoice_that_was_never_handed_over_is_untouched(self):
        invoice = self._invoice()
        self._pay(invoice)
        self.assertEqual(invoice.payment_state, "paid")
        self.assertFalse(invoice.debt_recovery_done)

    # ------------------------------------------------------------------
    # Dosarul
    # ------------------------------------------------------------------
    def test_the_case_details_are_kept_on_the_invoice(self):
        invoice = self._invoice()
        invoice.write(
            {
                "debt_state": "lawyer",
                "debt_law": "Cabinet Popescu",
                "debt_case_date": "2026-04-01",
                "debt_amount": 100.0,
                "debt_commission": 10.0,
                "debt_penalties": 5.0,
                "debt_recovery_text": "Trimis la avocat.",
            }
        )
        self.assertEqual(invoice.debt_state, "lawyer")
        self.assertEqual(invoice.debt_law, "Cabinet Popescu")
        self.assertEqual(invoice.debt_amount, 100.0)

    def test_the_fields_show_for_a_romanian_company(self):
        self.company.country_id = self.env.ref("base.ro")
        self.assertTrue(self._invoice(post=False).debt_company)

    def test_they_stay_hidden_elsewhere(self):
        self.company.country_id = self.env.ref("base.de")
        self.assertFalse(self._invoice(post=False).debt_company)

    def test_the_setting_follows_the_company(self):
        self.assertFalse(
            self.env["res.config.settings"]
            .create({})
            .account_allow_debt_recovery_invoice
        )
        self.company.account_allow_debt_recovery_invoice = True
        self.assertTrue(
            self.env["res.config.settings"]
            .create({})
            .account_allow_debt_recovery_invoice
        )
