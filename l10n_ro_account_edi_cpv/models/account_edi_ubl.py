# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import UserError


class AccountEdiXmlUBL20(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_20"

    def _get_invoice_line_item_vals(self, line, taxes_vals):
        vals = super()._get_invoice_line_item_vals(line, taxes_vals)
        if line.partner_id.l10n_ro_is_government_institution:
            if line.product_id.type == 'product':
                if not line.product_id.l10n_ro_cpv_code:
                    raise UserError(
                        _(
                            "Pentru acest partener este nevoie sa aveti completat codul CPV pe produse.",
                        )
                    )
                if line.product_id.l10n_ro_cpv_code:
                    vals["cpv"] = line.product_id.l10n_ro_cpv_code.code
                    vals["cpv_list"] = "STI"
        return vals
