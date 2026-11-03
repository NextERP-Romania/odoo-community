# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Taking in the self-invoices (autofacturi) customers issue in our name.

Such an invoice reaches the SPV with the company as supplier and the
customer as buyer. It is a sale of ours, so it must become a customer
invoice, never a vendor bill.
"""

import io
import zipfile
from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

COMPANY_VAT = "RO12345674"
CUSTOMER_VAT = "RO18547290"

XML = """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:efactura.mfinante.ro:CIUS-RO:1.0.1</cbc:CustomizationID>
  <cbc:ID>{number}</cbc:ID>
  <cbc:IssueDate>2026-10-01</cbc:IssueDate>
  <cbc:DueDate>2026-10-31</cbc:DueDate>
  <cbc:InvoiceTypeCode>{type_code}</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>RON</cbc:DocumentCurrencyCode>
  <cac:AccountingSupplierParty><cac:Party>
    <cac:PartyName><cbc:Name>Supplier</cbc:Name></cac:PartyName>
    <cac:PartyTaxScheme><cbc:CompanyID>{supplier}</cbc:CompanyID>
      <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:PartyTaxScheme>
    <cac:PartyLegalEntity><cbc:RegistrationName>Supplier</cbc:RegistrationName>
      <cbc:CompanyID>{supplier}</cbc:CompanyID></cac:PartyLegalEntity>
  </cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party>
    <cac:PartyName><cbc:Name>Customer</cbc:Name></cac:PartyName>
    <cac:PartyTaxScheme><cbc:CompanyID>{customer}</cbc:CompanyID>
      <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:PartyTaxScheme>
    <cac:PartyLegalEntity><cbc:RegistrationName>Customer</cbc:RegistrationName>
      <cbc:CompanyID>{customer}</cbc:CompanyID></cac:PartyLegalEntity>
  </cac:Party></cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="RON">21.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount currencyID="RON">100.00</cbc:TaxableAmount>
      <cbc:TaxAmount currencyID="RON">21.00</cbc:TaxAmount>
      <cac:TaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>21</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="RON">100.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="RON">100.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount currencyID="RON">121.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount currencyID="RON">121.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:ID>1</cbc:ID>
    <cbc:InvoicedQuantity unitCode="H87">1</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount currencyID="RON">100.00</cbc:LineExtensionAmount>
    <cac:Item><cbc:Name>Delivery services</cbc:Name>
      <cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>21</cbc:Percent>
        <cac:TaxScheme><cbc:ID>VAT</cbc:ID></cac:TaxScheme></cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price><cbc:PriceAmount currencyID="RON">100.00</cbc:PriceAmount></cac:Price>
  </cac:InvoiceLine>
</Invoice>
"""


def make_xml(
    number="AF-0001", supplier=COMPANY_VAT, customer=CUSTOMER_VAT, type_code="389"
):
    return XML.format(
        number=number, supplier=supplier, customer=customer, type_code=type_code
    ).encode()


@tagged("post_install_l10n", "post_install", "-at_install")
class TestAutoinvoice(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write(
            {
                "vat": COMPANY_VAT,
                "l10n_ro_edi_access_token": "token",
                "l10n_ro_create_customer_autoinvoice": True,
            }
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Customer",
                "is_company": True,
                "vat": CUSTOMER_VAT,
                "country_id": cls.env.ref("base.ro").id,
            }
        )
        cls.move_obj = cls.env["account.move"]

    def _autoinvoice_journal(self):
        return self.env["account.journal"].create(
            {
                "name": "Autofacturi Customer",
                "code": "AFC",
                "type": "sale",
                "company_id": self.company.id,
                "l10n_ro_sequence_type": "autoinv1",
                "l10n_ro_partner_id": self.customer.id,
            }
        )

    def _message(self, xml, index="5000000001", key="3000000001"):
        return {
            "id": key,
            "id_solicitare": index,
            "tip": "FACTURA PRIMITA",
            "answer": {
                "signature": {
                    "attachment_raw": b"<sig/>",
                    "key_signature": "SIG",
                    "key_certificate": "CERT",
                },
                "invoice": {"name": "AF-0001", "attachment_raw": xml},
            },
        }

    def _sync(self, received=(), sent=()):
        result = {
            "sent_invoices_accepted_messages": list(sent),
            "sent_invoices_refused_messages": [],
            "received_bills_messages": list(received),
            "errors": [],
        }
        with patch(
            "odoo.addons.l10n_ro_edi_extension.models.account_move."
            "_request_ciusro_synchronize_invoices",
            return_value=result,
        ):
            self.move_obj.with_company(self.company)._l10n_ro_edi_fetch_invoices()

    # ------------------------------------------------------------------
    # Recunoasterea autofacturii
    # ------------------------------------------------------------------
    def test_a_received_invoice_with_us_as_supplier_is_a_self_invoice(self):
        vat = self.move_obj._l10n_ro_edi_autoinvoice_customer_vat(
            self.company, make_xml(type_code="380")
        )
        self.assertEqual(vat, "18547290")

    def test_a_bill_from_a_supplier_is_not_a_self_invoice(self):
        xml = make_xml(supplier=CUSTOMER_VAT, customer=COMPANY_VAT)
        self.assertFalse(
            self.move_obj._l10n_ro_edi_autoinvoice_customer_vat(self.company, xml)
        )

    def test_a_sent_invoice_needs_the_self_billing_type_code(self):
        check = self.move_obj._l10n_ro_edi_autoinvoice_customer_vat
        self.assertFalse(check(self.company, make_xml(type_code="380"), received=False))
        self.assertTrue(check(self.company, make_xml(), received=False))

    def test_an_unreadable_xml_is_not_a_self_invoice(self):
        check = self.move_obj._l10n_ro_edi_autoinvoice_customer_vat
        self.assertFalse(check(self.company, b"not xml"))
        self.assertFalse(check(self.company, False))

    # ------------------------------------------------------------------
    # Crearea facturii
    # ------------------------------------------------------------------
    def test_in_the_customer_journal_it_is_posted_with_the_customer_number(self):
        journal = self._autoinvoice_journal()
        self._sync(received=[self._message(make_xml())])
        move = self.move_obj.search([("l10n_ro_edi_index", "=", "5000000001")])
        self.assertRecordValues(
            move,
            [
                {
                    "move_type": "out_invoice",
                    "journal_id": journal.id,
                    "partner_id": self.customer.id,
                    "name": "AF-0001",
                    "state": "posted",
                    "amount_total": 121.0,
                    "l10n_ro_edi_state": "invoice_validated",
                }
            ],
        )
        self.assertEqual(move.l10n_ro_edi_document_ids.key_signature, "SIG")

    def test_without_a_customer_journal_it_is_a_draft_in_the_first_sale_journal(
        self,
    ):
        first_sale = self.env["account.journal"].search(
            [
                *self.env["account.journal"]._check_company_domain(self.company),
                ("type", "=", "sale"),
            ],
            order="sequence, id",
            limit=1,
        )
        self._sync(received=[self._message(make_xml())])
        move = self.move_obj.search([("l10n_ro_edi_index", "=", "5000000001")])
        self.assertRecordValues(
            move,
            [
                {
                    "move_type": "out_invoice",
                    "journal_id": first_sale.id,
                    "partner_id": self.customer.id,
                    "state": "draft",
                    "l10n_ro_edi_state": "invoice_validated",
                }
            ],
        )

    def test_it_never_becomes_a_vendor_bill(self):
        self._sync(received=[self._message(make_xml())])
        bills = self.move_obj.search(
            [
                ("company_id", "=", self.company.id),
                ("move_type", "in", ("in_invoice", "in_refund")),
                ("l10n_ro_edi_index", "=", "5000000001"),
            ]
        )
        self.assertFalse(bills)

    def test_a_second_synchronization_does_not_duplicate_it(self):
        self._sync(received=[self._message(make_xml())])
        self._sync(received=[self._message(make_xml())])
        moves = self.move_obj.search([("l10n_ro_edi_index", "=", "5000000001")])
        self.assertEqual(len(moves), 1)

    def test_a_self_invoice_listed_as_sent_is_taken_in_too(self):
        self._sync(sent=[self._message(make_xml(), index="5000000002")])
        move = self.move_obj.search([("l10n_ro_edi_index", "=", "5000000002")])
        self.assertEqual(move.move_type, "out_invoice")

    # ------------------------------------------------------------------
    # Mesajul SPV al unei autofacturi aduse de "Synchronize with ANAF"
    # ------------------------------------------------------------------
    def _zip(self, xml, index="5000000001"):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zip_file:
            zip_file.writestr(f"{index}.xml", xml)
            zip_file.writestr(f"semnatura_{index}.xml", b"<sig/>")
        return buffer.getvalue()

    def _spv_message(self, zip_content=None, index="5000000001"):
        """The message as SPV Refresh creates it for a self-invoice: ANAF
        lists it without cif_emitent, so it keeps the company CIF."""
        message = self.env["l10n.ro.message.spv"].create(
            {
                "name": "3000000001",
                "request_id": index,
                "message_type": "in_invoice",
                "cif": "12345674",
                "company_id": self.company.id,
            }
        )
        if zip_content:
            attachment = self.env["ir.attachment"].create(
                {
                    "name": f"{index}.zip",
                    "raw": zip_content,
                    "mimetype": "application/zip",
                }
            )
            message.write({"attachment_id": attachment.id, "state": "downloaded"})
        return message

    def _get_invoice(self, message, download=None):
        """Run Get Invoice, with ANAF answering the ZIP download by
        ``download``."""
        with patch.object(
            type(self.env["l10n_ro_edi.document"]),
            "_request_ciusro_download_zip",
            return_value=download or {"error": "no download expected"},
        ) as download_zip:
            message.get_invoice_from_move()
        return download_zip

    def test_get_invoice_links_the_message_to_the_self_invoice(self):
        """The message keeps the company as partner, so the standard
        matching alone would not link it: Get Invoice gives it the customer
        of the self-invoice first."""
        self._autoinvoice_journal()
        self._sync(received=[self._message(make_xml())])
        message = self._spv_message(self._zip(make_xml()))
        download_zip = self._get_invoice(message)
        download_zip.assert_not_called()
        self.assertRecordValues(
            message,
            [
                {
                    "invoice_id": self.move_obj.search(
                        [("l10n_ro_edi_index", "=", "5000000001")]
                    ).id,
                    "partner_id": self.customer.id,
                    "l10n_ro_is_autoinvoice": True,
                    "message_type": "out_invoice",
                    "cif": "18547290",
                }
            ],
        )

    def test_get_invoice_downloads_the_missing_zip(self):
        """Get Invoice fills in the message without a separate Download."""
        self._autoinvoice_journal()
        self._sync(received=[self._message(make_xml())])
        message = self._spv_message()
        download_zip = self._get_invoice(
            message, download={"content": self._zip(make_xml())}
        )
        download_zip.assert_called_once()
        self.assertTrue(message.attachment_id)
        self.assertRecordValues(
            message,
            [
                {
                    "invoice_id": self.move_obj.search(
                        [("l10n_ro_edi_index", "=", "5000000001")]
                    ).id,
                    "partner_id": self.customer.id,
                    "l10n_ro_is_autoinvoice": True,
                    "cif": "18547290",
                    "ref": "AF-0001",
                    "invoice_amount": 121.0,
                }
            ],
        )

    def test_get_invoice_takes_the_customer_from_the_invoice_without_a_zip(self):
        """The download fails: the customer comes from the invoice."""
        self._autoinvoice_journal()
        self._sync(received=[self._message(make_xml())])
        message = self._spv_message()
        download_zip = self._get_invoice(
            message, download={"error": "Limita de descarcari"}
        )
        download_zip.assert_called_once()
        self.assertFalse(message.attachment_id)
        self.assertRecordValues(
            message,
            [
                {
                    "invoice_id": self.move_obj.search(
                        [("l10n_ro_edi_index", "=", "5000000001")]
                    ).id,
                    "partner_id": self.customer.id,
                    "l10n_ro_is_autoinvoice": True,
                    "cif": self.customer.l10n_ro_vat_number,
                }
            ],
        )

    def test_get_invoice_marks_only_invoices_of_a_self_invoicing_journal(self):
        """Without the customer journal the self-invoice is a draft in the
        first sale journal: the standard matching links its message by the
        SPV index, but the message is not marked and keeps the company CIF."""
        self._sync(received=[self._message(make_xml())])
        message = self._spv_message(self._zip(make_xml()))
        download_zip = self._get_invoice(message)
        download_zip.assert_not_called()
        self.assertRecordValues(
            message,
            [
                {
                    "invoice_id": self.move_obj.search(
                        [("l10n_ro_edi_index", "=", "5000000001")]
                    ).id,
                    "l10n_ro_is_autoinvoice": False,
                    "message_type": "in_invoice",
                    "cif": "12345674",
                }
            ],
        )

    def test_create_invoice_takes_in_the_self_invoice_as_a_customer_invoice(self):
        journal = self._autoinvoice_journal()
        message = self._spv_message(self._zip(make_xml()))
        message.get_xml_fom_zip()
        self.assertRecordValues(
            message,
            [
                {
                    "l10n_ro_is_autoinvoice": True,
                    "message_type": "out_invoice",
                    "cif": "18547290",
                }
            ],
        )
        message.create_invoice()
        self.assertRecordValues(
            message.invoice_id,
            [
                {
                    "move_type": "out_invoice",
                    "journal_id": journal.id,
                    "partner_id": self.customer.id,
                    "name": "AF-0001",
                    "l10n_ro_edi_download": "3000000001",
                }
            ],
        )

    # ------------------------------------------------------------------
    # Configurarea jurnalului
    # ------------------------------------------------------------------
    def test_the_journal_form_shows_the_fields_once(self):
        """Ours or l10n_ro_account_enterprise's, never both."""
        arch = self.env["account.journal"].get_view(view_type="form")["arch"]
        self.assertEqual(arch.count('name="l10n_ro_partner_id"'), 1)
        self.assertEqual(arch.count('name="l10n_ro_sequence_type"'), 1)

    # ------------------------------------------------------------------
    # Autofacturi emise de noi in numele furnizorului
    # ------------------------------------------------------------------
    def _export_vendor_document(self, move_type):
        move = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.customer.id,
                "invoice_date": "2026-10-01",
                "invoice_line_ids": [
                    Command.create(
                        {"name": "Delivery services", "quantity": 1, "price_unit": 100}
                    )
                ],
            }
        )
        move.action_post()
        xml, _errors = self.env["account.edi.xml.ubl_ro"]._export_invoice(move)
        return etree.fromstring(xml)

    def test_a_self_invoice_we_issue_has_type_code_389(self):
        tree = self._export_vendor_document("in_invoice")
        self.assertEqual(tree.findtext("./{*}InvoiceTypeCode"), "389")

    def test_a_self_billing_credit_note_has_type_code_381(self):
        """CIUS-RO accepts only 381; Odoo puts 261 on self-billing ones."""
        tree = self._export_vendor_document("in_refund")
        self.assertEqual(tree.findtext("./{*}CreditNoteTypeCode"), "381")

    def _supplier_autoinvoice(self, move_type="in_invoice"):
        journal = self.env["account.journal"].create(
            {
                "name": "Autofacturi Supplier",
                "code": "AFS",
                "type": "purchase",
                "company_id": self.company.id,
                "l10n_ro_sequence_type": "autoinv2",
                "l10n_ro_partner_id": self.customer.id,
            }
        )
        move = self.env["account.move"].create(
            {
                "move_type": move_type,
                "journal_id": journal.id,
                "partner_id": self.customer.id,
                "invoice_date": "2026-10-01",
                "invoice_line_ids": [
                    Command.create(
                        {"name": "Delivery services", "quantity": 1, "price_unit": 100}
                    )
                ],
            }
        )
        move.action_post()
        return move

    def _send(self, move, content):
        calls = []

        def fake_request(session, company, endpoint, params, data=None):
            calls.append({"endpoint": endpoint, "params": params})
            return {"content": content}

        with patch(
            "odoo.addons.l10n_ro_edi_autoinvoice.models.account_move."
            "make_efactura_request",
            side_effect=fake_request,
        ):
            errors = move._l10n_ro_edi_send_invoice(b"<Invoice/>")
        return calls, errors

    def test_a_self_invoice_we_issue_is_uploaded_as_autofactura(self):
        move = self._supplier_autoinvoice()
        self.assertTrue(move.is_l10n_ro_autoinvoice())
        calls, errors = self._send(
            move, b'<header ExecutionStatus="0" index_incarcare="5000000009"/>'
        )
        self.assertFalse(errors)
        self.assertEqual(
            calls[0]["params"],
            {"standard": "UBL", "cif": "12345674", "autofactura": "DA"},
        )
        self.assertEqual(move.l10n_ro_edi_index, "5000000009")
        self.assertEqual(move.l10n_ro_edi_state, "invoice_sent")

    def test_a_self_billing_credit_note_is_uploaded_as_cn(self):
        move = self._supplier_autoinvoice("in_refund")
        calls, _errors = self._send(
            move, b'<header ExecutionStatus="0" index_incarcare="5000000010"/>'
        )
        self.assertEqual(calls[0]["params"]["standard"], "CN")

    def test_the_spv_refusal_reason_is_kept(self):
        move = self._supplier_autoinvoice()
        _calls, errors = self._send(
            move,
            b'<header ExecutionStatus="1"><Errors errorMessage="CIF invalid"/>'
            b"</header>",
        )
        self.assertEqual(errors, ["CIF invalid"])

    def test_a_plain_vendor_bill_is_not_a_self_invoice(self):
        bill = self.env["account.move"].create(
            {"move_type": "in_invoice", "partner_id": self.customer.id}
        )
        self.assertFalse(bill.is_l10n_ro_autoinvoice())

    def _sync_own_supplier_autoinvoice(self):
        """Upload a supplier self-invoice, then get it back from the SPV as a
        received bill (FACTURA PRIMITA) before it is validated."""
        move = self._supplier_autoinvoice()
        self._send(move, b'<header ExecutionStatus="0" index_incarcare="5000000011"/>')
        xml = make_xml(number=move.name, supplier=CUSTOMER_VAT, customer=COMPANY_VAT)
        self._sync(received=[self._message(xml, index="5000000011")])
        return move

    def test_our_supplier_self_invoice_received_back_is_not_duplicated(self):
        move = self._sync_own_supplier_autoinvoice()
        bills = self.move_obj.search(
            [
                ("company_id", "=", self.company.id),
                ("move_type", "=", "in_invoice"),
                ("l10n_ro_edi_index", "=", "5000000011"),
            ]
        )
        self.assertEqual(bills, move)

    # ------------------------------------------------------------------
    # Fara bifa "Create Customer Self-Invoices" pe companie
    # ------------------------------------------------------------------
    def _disable_customer_autoinvoices(self):
        self.company.l10n_ro_create_customer_autoinvoice = False

    def test_without_the_setting_a_received_self_invoice_is_not_taken_in(self):
        """It is neither a customer invoice nor a vendor bill."""
        self._disable_customer_autoinvoices()
        self._autoinvoice_journal()
        self._sync(received=[self._message(make_xml())])
        self.assertFalse(
            self.move_obj.search([("l10n_ro_edi_index", "=", "5000000001")])
        )

    def test_without_the_setting_a_self_invoice_listed_as_sent_is_skipped(self):
        self._disable_customer_autoinvoices()
        self._sync(sent=[self._message(make_xml(), index="5000000002")])
        self.assertFalse(
            self.move_obj.search([("l10n_ro_edi_index", "=", "5000000002")])
        )

    def test_without_the_setting_create_invoice_still_takes_in_the_self_invoice(
        self,
    ):
        """The setting only drives the synchronization: Create Invoice on
        the SPV message still makes a customer invoice, never a vendor bill."""
        self._disable_customer_autoinvoices()
        journal = self._autoinvoice_journal()
        message = self._spv_message(self._zip(make_xml()))
        message.get_xml_fom_zip()
        self.assertTrue(message.l10n_ro_is_autoinvoice)
        message.create_invoice()
        self.assertRecordValues(
            message.invoice_id,
            [
                {
                    "move_type": "out_invoice",
                    "journal_id": journal.id,
                    "partner_id": self.customer.id,
                }
            ],
        )

    def test_without_the_setting_our_supplier_self_invoice_is_not_duplicated(self):
        self._disable_customer_autoinvoices()
        move = self._sync_own_supplier_autoinvoice()
        bills = self.move_obj.search(
            [
                ("company_id", "=", self.company.id),
                ("move_type", "=", "in_invoice"),
                ("l10n_ro_edi_index", "=", "5000000011"),
            ]
        )
        self.assertEqual(bills, move)
