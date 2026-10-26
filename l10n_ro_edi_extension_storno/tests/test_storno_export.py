# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Customer credit notes sent to ANAF as storno invoices.

With the company setting on, an ``out_refund`` is exported as a UBL
``Invoice`` with type code 380, negative quantities and amounts, a positive
item price (BR-27) and a reference to the reversed invoice (BT-25 / BT-26).
With the setting off, the standard ``CreditNote`` 381 is left untouched.
"""

from lxml import etree

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

NS = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}


@tagged("post_install_l10n", "post_install", "-at_install")
class TestStornoExport(AccountTestInvoicingCommon):
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

        cls.invoice = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner_ro.id,
                "invoice_date": "2026-10-01",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.product_a.id,
                            "quantity": 10,
                            "price_unit": 100.0,
                            "tax_ids": [Command.set(cls.tax_21.ids)],
                        }
                    )
                ],
            }
        )
        cls.invoice.action_post()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _reverse(self, quantity=None):
        """Credit note created with the 'Reverse' button, optionally partial."""
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=self.invoice.ids)
            .create(
                {
                    "reason": "Retur",
                    "journal_id": self.invoice.journal_id.id,
                    "date": "2026-10-15",
                }
            )
        )
        refund = self.env["account.move"].browse(wizard.refund_moves()["res_id"])
        if quantity is not None:
            refund.invoice_line_ids.quantity = quantity
        refund.action_post()
        return refund

    def _export(self, move):
        xml, errors = self.ubl._export_invoice(move)
        self.assertFalse(errors)
        return etree.fromstring(xml)

    def _text(self, root, xpath):
        return root.findtext(xpath, namespaces=NS)

    def _float(self, root, xpath):
        return float(self._text(root, xpath))

    # ------------------------------------------------------------------
    # Setting off: standard credit note
    # ------------------------------------------------------------------
    def test_setting_off_keeps_credit_note_381(self):
        self.company.l10n_ro_credit_note_einvoice = False
        root = self._export(self._reverse(quantity=4))

        self.assertEqual(etree.QName(root).localname, "CreditNote")
        self.assertEqual(self._text(root, "cbc:CreditNoteTypeCode"), "381")
        self.assertEqual(
            self._float(root, "cac:CreditNoteLine/cbc:CreditedQuantity"), 4.0
        )
        self.assertEqual(
            self._float(root, "cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount"), 484.0
        )
        self.assertIsNone(root.find("cac:BillingReference", NS))

    # ------------------------------------------------------------------
    # Setting on: storno invoice 380
    # ------------------------------------------------------------------
    def test_partial_credit_note_is_invoice_380_with_negative_values(self):
        self.company.l10n_ro_credit_note_einvoice = True
        root = self._export(self._reverse(quantity=4))

        self.assertEqual(etree.QName(root).localname, "Invoice")
        self.assertEqual(self._text(root, "cbc:InvoiceTypeCode"), "380")
        self.assertIsNone(root.find("cbc:CreditNoteTypeCode", NS))
        self.assertFalse(root.findall("cac:CreditNoteLine", NS))

        line = "cac:InvoiceLine"
        self.assertEqual(self._float(root, f"{line}/cbc:InvoicedQuantity"), -4.0)
        self.assertEqual(self._float(root, f"{line}/cbc:LineExtensionAmount"), -400.0)
        # BR-27: the item net price (BT-146) is never negative.
        self.assertEqual(self._float(root, f"{line}/cac:Price/cbc:PriceAmount"), 100.0)

        self.assertEqual(self._float(root, "cac:TaxTotal/cbc:TaxAmount"), -84.0)
        subtotal = "cac:TaxTotal/cac:TaxSubtotal"
        self.assertEqual(self._float(root, f"{subtotal}/cbc:TaxableAmount"), -400.0)
        self.assertEqual(self._float(root, f"{subtotal}/cbc:TaxAmount"), -84.0)

        total = "cac:LegalMonetaryTotal"
        self.assertEqual(self._float(root, f"{total}/cbc:LineExtensionAmount"), -400.0)
        self.assertEqual(self._float(root, f"{total}/cbc:TaxExclusiveAmount"), -400.0)
        self.assertEqual(self._float(root, f"{total}/cbc:TaxInclusiveAmount"), -484.0)

    def test_total_credit_note_mirrors_the_invoice(self):
        self.company.l10n_ro_credit_note_einvoice = True
        invoice_root = self._export(self.invoice)
        refund_root = self._export(self._reverse())

        self.assertEqual(self._text(refund_root, "cbc:InvoiceTypeCode"), "380")
        for xpath in (
            "cac:InvoiceLine/cbc:InvoicedQuantity",
            "cac:InvoiceLine/cbc:LineExtensionAmount",
            "cac:TaxTotal/cbc:TaxAmount",
            "cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount",
            "cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount",
        ):
            self.assertEqual(
                self._float(refund_root, xpath),
                -self._float(invoice_root, xpath),
                xpath,
            )
        self.assertEqual(
            self._float(refund_root, "cac:InvoiceLine/cac:Price/cbc:PriceAmount"),
            self._float(invoice_root, "cac:InvoiceLine/cac:Price/cbc:PriceAmount"),
        )

    def test_storno_invoice_references_the_original_invoice(self):
        self.company.l10n_ro_credit_note_einvoice = True
        root = self._export(self._reverse(quantity=4))

        reference = "cac:BillingReference/cac:InvoiceDocumentReference"
        self.assertEqual(self._text(root, f"{reference}/cbc:ID"), self.invoice.name)
        self.assertEqual(self._text(root, f"{reference}/cbc:IssueDate"), "2026-10-01")

    def test_credit_note_without_origin_has_no_billing_reference(self):
        self.company.l10n_ro_credit_note_einvoice = True
        refund = self.env["account.move"].create(
            {
                "move_type": "out_refund",
                "partner_id": self.partner_ro.id,
                "invoice_date": "2026-10-15",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": 1,
                            "price_unit": 50.0,
                            "tax_ids": [Command.set(self.tax_21.ids)],
                        }
                    )
                ],
            }
        )
        refund.action_post()
        root = self._export(refund)

        self.assertEqual(self._text(root, "cbc:InvoiceTypeCode"), "380")
        self.assertEqual(
            self._float(root, "cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount"), -60.5
        )
        self.assertIsNone(root.find("cac:BillingReference", NS))

    def test_customer_invoice_is_not_changed(self):
        self.company.l10n_ro_credit_note_einvoice = True
        root = self._export(self.invoice)

        self.assertEqual(self._text(root, "cbc:InvoiceTypeCode"), "380")
        self.assertEqual(
            self._float(root, "cac:InvoiceLine/cbc:InvoicedQuantity"), 10.0
        )
        self.assertEqual(
            self._float(root, "cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount"), 1210.0
        )
        self.assertIsNone(root.find("cac:BillingReference", NS))

    def test_no_document_type_code_50_on_storno_invoice(self):
        """DocumentTypeCode 50 is only allowed on a CreditNote (UBL-SR-43)."""
        refund = self._reverse(quantity=4)
        self.company.l10n_ro_credit_note_einvoice = False
        self.assertEqual(
            self.ubl._get_document_type_code_node(refund, {}), {"_text": "50"}
        )
        self.company.l10n_ro_credit_note_einvoice = True
        self.assertIsNone(self.ubl._get_document_type_code_node(refund, {}))

    # ------------------------------------------------------------------
    # PDF report
    # ------------------------------------------------------------------
    def _render_html(self, move):
        html, _type = self.env["ir.actions.report"]._render_qweb_html(
            "account.account_invoices", move.ids
        )
        # Odoo puts an invisible character after the minus sign and
        # non-breaking spaces inside amounts; drop them to compare plain
        # numbers.
        html = html.decode()
        for char in ("﻿", "​"):
            html = html.replace(char, "")
        return html.replace("\xa0", " ")

    def test_pdf_setting_off_keeps_credit_note(self):
        self.company.l10n_ro_credit_note_einvoice = False
        html = self._render_html(self._reverse(quantity=4))

        self.assertIn("Credit Note", html)
        self.assertNotIn("Reversal of invoice", html)
        self.assertNotIn("-400.00", html)
        self.assertNotIn("-484.00", html)

    def test_pdf_storno_invoice_has_negative_values_and_reference(self):
        self.company.l10n_ro_credit_note_einvoice = True
        html = self._render_html(self._reverse(quantity=4))

        self.assertNotIn("Credit Note", html)
        self.assertIn("Invoice Date", html)
        self.assertIn("Reversal of invoice", html)
        self.assertIn(self.invoice.name, html)
        for amount in ("-4.00", "-400.00", "-84.00", "-484.00"):
            self.assertIn(amount, html)
        # The unit price stays positive.
        self.assertIn("100.00", html)
        self.assertNotIn("-100.00", html)

    def test_pdf_customer_invoice_is_not_changed(self):
        self.company.l10n_ro_credit_note_einvoice = True
        html = self._render_html(self.invoice)

        self.assertNotIn("Reversal of invoice", html)
        self.assertIn("1,210.00", html)
        self.assertNotIn("-1,210.00", html)

    # ------------------------------------------------------------------
    # Negation helper
    # ------------------------------------------------------------------
    def test_negate_helper_keeps_prices_and_the_original(self):
        values = {
            "quantity": 4.0,
            "price_unit": 100.0,
            "price_subtotal": 400.0,
            "tax_amount_currency": 84.0,
            "currency_pd": 0.01,
            "is_refund": False,
            "subtotals": [{"base_amount": 400.0, "name": "Untaxed Amount"}],
        }
        negated = self.env["account.move"]._l10n_ro_storno_negate(values)

        self.assertEqual(negated["quantity"], -4.0)
        self.assertEqual(negated["price_subtotal"], -400.0)
        self.assertEqual(negated["tax_amount_currency"], -84.0)
        self.assertEqual(negated["subtotals"][0]["base_amount"], -400.0)
        self.assertEqual(negated["price_unit"], 100.0)
        self.assertEqual(negated["currency_pd"], 0.01)
        self.assertIs(negated["is_refund"], False)
        # The original (e.g. the cached tax_totals) is not modified.
        self.assertEqual(values["quantity"], 4.0)
        self.assertEqual(values["subtotals"][0]["base_amount"], 400.0)

    def test_zero_amounts_do_not_become_negative_zero(self):
        node = {"_text": 0.0}
        self.ubl._ro_negate_amount(node)
        self.assertEqual(node["_text"], 0.0)
        self.assertNotIn("-", str(node["_text"]))
