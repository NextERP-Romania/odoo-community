# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

from odoo import _, api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("pricelist_id")
    def _onchange_pricelist_id_show_update_prices(self):
        res = super()._onchange_pricelist_id_show_update_prices()
        if (
            self.order_line
            and self.pricelist_id
            and self._origin.pricelist_id != self.pricelist_id
        ):
            if self.company_id.sale_auto_update_price:
                self._recompute_prices()
                if not isinstance(self.id, models.NewId):
                    self.message_post(
                        body=_(
                            "Product prices have been recomputed according to pricelist "
                            "<b>%s<b> ",
                            self.pricelist_id.display_name,
                        )
                    )

        return res
