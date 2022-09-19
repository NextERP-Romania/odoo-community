# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import _, api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("pricelist_id", "order_line")
    def _onchange_pricelist_id(self):
        res = super()._onchange_pricelist_id()
        if (
            self.order_line
            and self.pricelist_id
            and self._origin.pricelist_id != self.pricelist_id
        ):
            if self.company_id.sale_auto_update_price:
                for line in self._get_update_prices_lines():
                    line.product_uom_change()
                    # Force 0 as discount for the cases when _onchange_discount directly returns
                    line.discount = 0
                    line._onchange_discount()
                self.show_update_pricelist = False
                self._origin.message_post(
                    body=_(
                        "Product prices have been recomputed according to pricelist <b>%s<b> ",
                        self.pricelist_id.display_name,
                    )
                )

        return res
