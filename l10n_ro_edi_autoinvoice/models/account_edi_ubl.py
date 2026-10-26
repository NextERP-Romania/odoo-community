# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountEdiXmlUBLRO(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_ro"

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
