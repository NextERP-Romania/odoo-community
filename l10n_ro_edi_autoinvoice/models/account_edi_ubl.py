# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountEdiXmlUBLRO(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_ro"

    def _add_invoice_header_nodes(self, document_node, vals):
        res = super()._add_invoice_header_nodes(document_node, vals)
        # Odoo exports every vendor refund as a self-billing credit note,
        # with CreditNoteTypeCode 261. CIUS-RO accepts only 381, also on the
        # self-billing credit notes we issue in a supplier's name.
        if self._is_document(vals, "self_credit_note"):
            document_node["cbc:CreditNoteTypeCode"] = {"_text": 381}
        return res

    def _import_retrieve_customer(self, collected_values):
        # A self-invoice is imported for a customer already found by its VAT:
        # keep it, even when its VAT is stored without the RO prefix, which
        # would otherwise make the import create a duplicate partner.
        partner_id = self.env.context.get("l10n_ro_autoinvoice_partner_id")
        if not partner_id:
            return super()._import_retrieve_customer(collected_values)
        collected_values["customer_values"]["customer"] = self.env[
            "res.partner"
        ].browse(partner_id)
        collected_values["to_write"]["partner_id"] = partner_id

    def _import_create_missing_customer(self, collected_values):
        if self.env.context.get("l10n_ro_autoinvoice_partner_id"):
            return
        return super()._import_create_missing_customer(collected_values)
