# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Invoice note (BT-22) kept inside what ANAF accepts.

ANAF refuses an invoice with more than 20 cbc:Note (BR-RO-A020). The invoice
must still be posted and sent: only the first notes, cut to their maximum
length, go into the XML and the rest of the text is dropped.
"""

from lxml import etree

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.l10n_ro_edi_extension_limits.models.account_edi_ubl_limits import (
    _INVOICE_NOTE_MAX_COUNT,
    _INVOICE_NOTE_MAX_LEN,
)

NS = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}


@tagged("post_install_l10n", "post_install", "-at_install")
class TestInvoiceNoteLimits(AccountTestInvoicingCommon):
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
                "vat": "RO1234567897",
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _invoice(self, narration):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_ro.id,
                "invoice_date": "2026-11-10",
                "narration": narration,
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
        invoice.action_post()
        return invoice

    def _notes(self, invoice):
        xml, errors = self.ubl._export_invoice(invoice)
        self.assertFalse(errors)
        root = etree.fromstring(xml)
        return [n.text for n in root.findall("cbc:Note", NS)]

    # ------------------------------------------------------------------
    # The finished invoice XML
    # ------------------------------------------------------------------
    def test_a_long_note_is_capped_in_count_and_length(self):
        """The case refused by ANAF: a note long enough for 20+ pieces."""
        invoice = self._invoice("<p>" + "Comentariu factura. " * 400 + "</p>")
        notes = self._notes(invoice)
        self.assertEqual(len(notes), _INVOICE_NOTE_MAX_COUNT)
        self.assertTrue(all(len(n) <= _INVOICE_NOTE_MAX_LEN for n in notes))

    def test_the_kept_text_is_the_start_of_the_note(self):
        invoice = self._invoice("<p>INCEPUT " + "x" * 5000 + " SFARSIT</p>")
        notes = self._notes(invoice)
        self.assertTrue(notes[0].startswith("INCEPUT"))
        self.assertNotIn("SFARSIT", " ".join(notes))

    def test_a_short_note_is_sent_whole(self):
        invoice = self._invoice("<p>Conditii de plata: 100% avans</p>")
        self.assertEqual(self._notes(invoice), ["Conditii de plata: 100% avans"])

    def test_an_invoice_without_note_has_no_note(self):
        self.assertEqual(self._notes(self._invoice(False)), [])

    # ------------------------------------------------------------------
    # The final pass on the document node
    # ------------------------------------------------------------------
    def test_notes_added_by_other_modules_are_capped_too(self):
        document = {"cbc:Note": [{"_text": "n" * 500} for _ in range(30)]}
        self.ubl._ro_apply_invoice_note_limits(document)
        self.assertEqual(len(document["cbc:Note"]), _INVOICE_NOTE_MAX_COUNT)
        for note in document["cbc:Note"]:
            self.assertEqual(len(note["_text"]), _INVOICE_NOTE_MAX_LEN)

    def test_a_single_note_node_is_kept_and_cut(self):
        document = {"cbc:Note": {"_text": "n" * 500}}
        self.ubl._ro_apply_invoice_note_limits(document)
        self.assertEqual(len(document["cbc:Note"]), 1)
        self.assertEqual(len(document["cbc:Note"][0]["_text"]), _INVOICE_NOTE_MAX_LEN)

    def test_empty_notes_are_dropped(self):
        document = {"cbc:Note": [{"_text": None}, {"_text": "Nota"}, {"_text": ""}]}
        self.ubl._ro_apply_invoice_note_limits(document)
        self.assertEqual(document["cbc:Note"], [{"_text": "Nota"}])

    def test_a_document_without_notes_is_untouched(self):
        document = {"cbc:ID": {"_text": "F-0001"}}
        self.ubl._ro_apply_invoice_note_limits(document)
        self.assertEqual(document, {"cbc:ID": {"_text": "F-0001"}})
