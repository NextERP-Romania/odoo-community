# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Deleting the last invoice of a journal without leaving a hole.

Core lets a drafted-back invoice go but keeps its number spent, so the next
invoice skips one. With the setting on, the number of the last invoice goes
back to the sequence and the next invoice takes it.
"""

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestDeleteLastInvoice(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.journal = cls.company_data["default_journal_sale"].copy(
            {"name": "Vanzari test", "code": "VTST"}
        )

    def _invoice(self, post=True):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "journal_id": self.journal.id,
                "invoice_date": "2026-03-15",
                "invoice_line_ids": [
                    (0, 0, {"product_id": self.product_a.id, "price_unit": 100.0})
                ],
            }
        )
        if post:
            move.action_post()
        return move

    def _delete(self, move):
        move.button_draft()
        move.unlink()

    def test_without_the_setting_the_number_stays_spent(self):
        """That is core's behaviour, and what this module exists to
        change."""
        self._invoice()
        self._delete(self._invoice())
        self.assertTrue(self._invoice().name.endswith("00003"))

    def test_the_number_of_the_last_invoice_goes_back(self):
        self.company.account_allow_delete_last_invoice = True
        self._invoice()
        second = self._invoice()
        name = second.name
        self._delete(second)
        self.assertEqual(self._invoice().name, name)

    def test_the_only_invoice_of_a_journal_gives_its_number_back_too(self):
        """Nothing precedes it, so the journal has to start over at one."""
        self.company.account_allow_delete_last_invoice = True
        first = self._invoice()
        name = first.name
        self._delete(first)
        self.assertEqual(self._invoice().name, name)

    def test_an_invoice_that_is_not_the_last_one_leaves_the_sequence_alone(self):
        """Handing back a number from the middle would hand out a duplicate."""
        self.company.account_allow_delete_last_invoice = True
        first = self._invoice()
        second = self._invoice()
        self._delete(first)
        self.assertTrue(self._invoice().name > second.name)

    def test_the_deleted_invoice_is_really_gone(self):
        self.company.account_allow_delete_last_invoice = True
        invoice = self._invoice()
        self._delete(invoice)
        self.assertFalse(invoice.exists())

    def test_a_draft_that_was_never_numbered_goes_as_always(self):
        draft = self._invoice(post=False)
        draft.unlink()
        self.assertFalse(draft.exists())

    def test_the_setting_follows_the_company(self):
        self.assertFalse(
            self.env["res.config.settings"].create({}).account_allow_delete_last_invoice
        )
        self.company.account_allow_delete_last_invoice = True
        self.assertTrue(
            self.env["res.config.settings"].create({}).account_allow_delete_last_invoice
        )
