# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_down_payment_line_values_from_base_line(self, base_line):
        values = super()._prepare_down_payment_line_values_from_base_line(base_line)
        product = self.company_id.l10n_ro_sale_down_payment_product_id
        if product:
            values.update(
                {
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    # avoid pricelist discount computed from the product
                    "discount": 0.0,
                }
            )
        return values
