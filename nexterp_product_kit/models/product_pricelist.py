# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).
import logging

from odoo import models

_loger = logging.getLogger(__name__)


class ProductPircelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products, qty, uom=None, date=False, **kwargs):
        res = super()._compute_price_rule(products, qty, uom, date, **kwargs)
        for product in products:
            if product._name == "product.product" and product.kit_product_ids:
                new_price = 0
                product_uom = product.uom_id
                target_uom = uom or product_uom
                if target_uom != product_uom:
                    qty_in_product_uom = target_uom._compute_quantity(
                        qty, product_uom, raise_if_failure=False
                    )
                else:
                    qty_in_product_uom = qty
                for kit_line in product.kit_product_ids:
                    quantity = qty_in_product_uom * kit_line.product_qty
                    kit_price = self._compute_price_rule(
                        kit_line.component_product_id,
                        quantity,
                        kit_line.component_product_id.uom_id,
                        date,
                        **kwargs
                    )[kit_line.component_product_id.id]
                    new_price += kit_price[0] * quantity
                res[product.id] = (new_price, False)
        return res
