# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("product_id", "linked_line_id", "linked_line_ids")
    def _compute_name(self):
        res = super()._compute_name()
        # Keep the standard down payment description even if a product is set
        for line in self.filtered(
            lambda sol: sol.is_downpayment and sol.product_id and not sol.display_type
        ):
            lang = line.order_id._get_lang()
            if lang != self.env.lang:
                line = line.with_context(lang=lang)
            line.name = line._get_downpayment_description()
        return res
