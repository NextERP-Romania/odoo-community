# Copyright (C) 2026 NextERP Romania
# License LGPL-3 or later
"""Which journals go to e-Factura.

Core sends every Romanian customer invoice; here the journal decides, so a
company can keep an internal sales journal out of ANAF.
"""

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestEdiPerJournal(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.company_data["default_journal_sale"]
        cls.Send = cls.env["account.move.send"]

    def _invoice(self, journal=None):
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "journal_id": (journal or self.journal).id,
                "invoice_date": "2026-03-15",
                "invoice_line_ids": [
                    (0, 0, {"product_id": self.product_a.id, "price_unit": 100.0})
                ],
            }
        )

    def test_a_journal_is_kept_out_of_edi_until_it_is_turned_on(self):
        self.journal.l10n_ro_edi_send_enabled = False
        self.assertFalse(self.Send._is_ro_edi_applicable(self._invoice()))

    def test_turning_the_journal_on_lets_its_invoices_through(self):
        self.journal.l10n_ro_edi_send_enabled = True
        self.assertTrue(self.Send._is_ro_edi_applicable(self._invoice()))

    def test_one_journal_on_does_not_open_the_others(self):
        other = self.journal.copy({"name": "Vanzari interne", "code": "VINT"})
        self.journal.l10n_ro_edi_send_enabled = True
        other.l10n_ro_edi_send_enabled = False
        self.assertTrue(self.Send._is_ro_edi_applicable(self._invoice()))
        self.assertFalse(self.Send._is_ro_edi_applicable(self._invoice(other)))

    def test_the_flag_is_off_on_a_new_journal(self):
        self.assertFalse(
            self.env["account.journal"]
            .create({"name": "Nou", "code": "NOU", "type": "sale"})
            .l10n_ro_edi_send_enabled
        )
