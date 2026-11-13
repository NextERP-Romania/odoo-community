from odoo import models

from odoo.addons.account_edi_ubl_cii.models.account_edi_common import FloatFmt

# LegalMonetaryTotal amounts negated when a credit note is exported as a
# storno invoice (380 with negative values).
_STORNO_MONETARY_TOTAL_TAGS = (
    "cbc:LineExtensionAmount",
    "cbc:TaxExclusiveAmount",
    "cbc:TaxInclusiveAmount",
    "cbc:AllowanceTotalAmount",
    "cbc:ChargeTotalAmount",
    "cbc:PrepaidAmount",
    "cbc:PayableRoundingAmount",
    "cbc:PayableAmount",
)


class AccountEdiXmlUBLRO(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_ro"

    # ------------------------------------------------------------------
    # Storno: customer credit note exported as invoice 380
    # ------------------------------------------------------------------

    def _ro_is_storno_refund(self, invoice):
        return (
            bool(invoice)
            and invoice.move_type == "out_refund"
            and invoice.company_id.l10n_ro_credit_note_einvoice
        )

    def _ubl_add_values_document_type(self, vals):
        res = super()._ubl_add_values_document_type(vals)
        if self._ro_is_storno_refund(vals["invoice"]):
            self._define_document_type(vals, "invoice")
        return res

    def _add_invoice_config_vals(self, vals):
        # Root <Invoice>, cbc:InvoiceTypeCode 380, cac:InvoiceLine and
        # cbc:InvoicedQuantity instead of the CreditNote structure.
        res = super()._add_invoice_config_vals(vals)
        if self._ro_is_storno_refund(vals["invoice"]):
            vals["document_type"] = "invoice"
        return res

    def _ubl_add_billing_reference_nodes(self, vals):
        # BT-25 / BT-26 — preceding invoice number and issue date.
        res = super()._ubl_add_billing_reference_nodes(vals)
        invoice = vals["invoice"]
        origin = invoice.reversed_entry_id
        if self._ro_is_storno_refund(invoice) and origin:
            vals["document_node"]["cac:BillingReference"] = [
                {
                    "cac:InvoiceDocumentReference": {
                        "cbc:ID": {"_text": origin.name},
                        "cbc:IssueDate": {"_text": origin.invoice_date},
                    }
                }
            ]
        return res

    def _get_document_type_code_node(self, invoice, invoice_data):
        # DocumentTypeCode '50' is only allowed on a CreditNote (UBL-SR-43).
        if self._ro_is_storno_refund(invoice):
            return None
        return super()._get_document_type_code_node(invoice, invoice_data)

    def _get_invoice_node(self, vals):
        document_node = super()._get_invoice_node(vals)
        if (
            self._ro_is_storno_refund(vals["invoice"])
            and vals["document_type"] == "invoice"
        ):
            self._ro_apply_storno_signs(document_node)
        return document_node

    # ------------------------------------------------------------------
    # Storno: negative quantities and amounts on the exported invoice
    # ------------------------------------------------------------------

    def _ro_negate_amount(self, node):
        if not isinstance(node, dict):
            return
        value = node.get("_text")
        if not isinstance(value, (int, float)) or not value:
            return
        if isinstance(value, FloatFmt):
            node["_text"] = FloatFmt(
                -float(value), min_dp=value.min_dp, max_dp=value.max_dp
            )
        else:
            node["_text"] = -value

    def _ro_negate_allowance_charges(self, parent):
        for allowance in self._ro_iter_children(parent, "cac:AllowanceCharge"):
            self._ro_negate_amount(allowance.get("cbc:Amount"))
            self._ro_negate_amount(allowance.get("cbc:BaseAmount"))

    def _ro_negate_tax_totals(self, parent):
        for tax_total in self._ro_iter_children(parent, "cac:TaxTotal"):
            self._ro_negate_amount(tax_total.get("cbc:TaxAmount"))
            for subtotal in self._ro_iter_children(tax_total, "cac:TaxSubtotal"):
                self._ro_negate_amount(subtotal.get("cbc:TaxableAmount"))
                self._ro_negate_amount(subtotal.get("cbc:TaxAmount"))

    def _ro_apply_storno_signs(self, document_node):
        # The item net price (BT-146) stays positive (BR-27), only
        # quantities and amounts carry the minus sign.
        for line in self._ro_iter_children(document_node, "cac:InvoiceLine"):
            self._ro_negate_amount(line.get("cbc:InvoicedQuantity"))
            self._ro_negate_amount(line.get("cbc:LineExtensionAmount"))
            self._ro_negate_allowance_charges(line)
            self._ro_negate_tax_totals(line)

        self._ro_negate_allowance_charges(document_node)
        self._ro_negate_tax_totals(document_node)

        monetary_total = document_node.get("cac:LegalMonetaryTotal")
        if isinstance(monetary_total, dict):
            for tag in _STORNO_MONETARY_TOTAL_TAGS:
                self._ro_negate_amount(monetary_total.get(tag))
