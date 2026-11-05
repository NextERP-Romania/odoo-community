# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import models

# "Factură - informații în scopuri contabile": an invoice issued for a sale
# already declared on a fiscal receipt.
RECEIPT_INVOICE_TYPE_CODE = 751


class AccountEdiXmlUBLRO(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_ro"

    def _l10n_ro_is_receipt_invoice(self, invoice):
        return bool(
            invoice
            and invoice.move_type == "out_invoice"
            and invoice.l10n_ro_fiscal_receipt_number
        )

    def _add_invoice_header_nodes(self, document_node, vals):
        res = super()._add_invoice_header_nodes(document_node, vals)
        # Only on an invoice: a credit note keeps its own type code, and a
        # self-billing invoice is never issued for a receipt.
        if (
            vals.get("document_type") == "invoice"
            and vals.get("process_type") != "selfbilling"
            and self._l10n_ro_is_receipt_invoice(vals["invoice"])
        ):
            document_node["cbc:InvoiceTypeCode"] = {"_text": RECEIPT_INVOICE_TYPE_CODE}
        return res
