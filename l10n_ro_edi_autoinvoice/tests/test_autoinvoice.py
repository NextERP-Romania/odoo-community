# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Taking in the self-invoices (autofacturi) customers issue in our name.

Such an invoice reaches the SPV with the company as supplier and the
customer as buyer. It is a sale of ours, so it must become a customer
invoice, never a vendor bill.
"""

from unittest.mock import patch

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
        cls.company.write({"vat": COMPANY_VAT, "l10n_ro_edi_access_token": "token"})
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Customer",
                "is_company": True,
                "vat": CUSTOMER_VAT,
                "country_id": cls.env.ref("base.ro").id,
            }
        )
        cls.move_obj = cls.env["account.move"]
        cls.has_journal_fields = {
            "l10n_ro_partner_id",
            "l10n_ro_sequence_type",
        } <= set(cls.env["account.journal"]._fields)

    def _autoinvoice_journal(self):
        if not self.has_journal_fields:
            self.skipTest("The RO journal fields are not installed.")
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
