# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""An invoice issued for a fiscal receipt goes to e-Factura as 751.

The sale and its VAT were declared with the receipt; the invoice the
customer asked for afterwards is sent for accounting purposes only, with
type code 751. Any other invoice keeps 380.
"""

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

NS = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


@tagged("post_install_l10n", "post_install", "-at_install")
class TestReceiptInvoiceExport(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write(
            {
                "state_id": cls.env.ref("base.RO_B").id,
                "city": "SECTOR1",
                "zip": "010101",
                "vat": "RO1234567897",
                "street": "Strada Test, 3",
            }
        )
        cls.partner_ro = cls.env["res.partner"].create(
            {
                "name": "Romanian Test Partner",
                "is_company": True,
                "country_id": cls.env.ref("base.ro").id,
                "state_id": cls.env.ref("base.RO_B").id,
                "city": "SECTOR3",
                "zip": "010101",
                "vat": "RO18547290",
                "street": "Strada Partner, 88",
            }
        )
        cls.tax_21 = cls.env["account.tax"].create(
            {
                "name": "tax_21",
                "amount_type": "percent",
                "amount": 21,
                "type_tax_use": "sale",
                "country_id": cls.env.ref("base.ro").id,
            }
        )
        cls.ubl = cls.env["account.edi.xml.ubl_ro"]

    def _invoice(self, receipt=None, move_type="out_invoice"):
        move = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_ro.id,
                "invoice_date": "2026-11-05",
                "l10n_ro_fiscal_receipt_number": receipt,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [Command.set(self.tax_21.ids)],
                        }
                    )
                ],
            }
        )
        move.action_post()
        return move

    def _type_code(self, move, tag="cbc:InvoiceTypeCode"):
        xml, errors = self.ubl._export_invoice(move)
        self.assertFalse(errors)
        return etree.fromstring(xml).findtext(tag, namespaces=NS)

    def test_an_invoice_for_a_fiscal_receipt_is_751(self):
        self.assertEqual(self._type_code(self._invoice(receipt="0000042")), "751")

    def test_any_other_invoice_keeps_380(self):
        self.assertEqual(self._type_code(self._invoice()), "380")

    def test_a_credit_note_keeps_its_own_type_code(self):
        refund = self._invoice(receipt="0000042", move_type="out_refund")
        self.assertEqual(self._type_code(refund, "cbc:CreditNoteTypeCode"), "381")

    def test_the_receipt_number_is_fixed_once_posted(self):
        move = self._invoice(receipt="0000042")
        with self.assertRaises(UserError):
            move.l10n_ro_fiscal_receipt_number = "0000043"
        with self.assertRaises(UserError):
            move.l10n_ro_fiscal_receipt_number = False
        # Writing the same value is harmless.
        move.l10n_ro_fiscal_receipt_number = "0000042"
        self.assertEqual(self._type_code(move), "751")

    def test_the_receipt_number_is_free_on_a_draft(self):
        move = self._invoice(receipt="0000042")
        move.button_draft()
        move.l10n_ro_fiscal_receipt_number = "0000043"
        self.assertEqual(move.l10n_ro_fiscal_receipt_number, "0000043")

    def test_flow_receipt_invoice_draft_to_posted(self):
        """Set on the draft, fixed on the posted invoice, sent as 751; the
        chatter and the other non-fiscal fields stay writable."""
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_ro.id,
                "invoice_date": "2026-11-05",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [Command.set(self.tax_21.ids)],
                        }
                    )
                ],
            }
        )
        move.l10n_ro_fiscal_receipt_number = "0000042"
        move.action_post()
        self.assertEqual(move.state, "posted")
        self.assertEqual(move.amount_total, 121.0)
        with self.assertRaises(UserError):
            move.l10n_ro_fiscal_receipt_number = "0000099"
        self.assertEqual(move.l10n_ro_fiscal_receipt_number, "0000042")
        move.message_post(body="Nota")
        move.narration = "Observatie"
        self.assertEqual(self._type_code(move), "751")
