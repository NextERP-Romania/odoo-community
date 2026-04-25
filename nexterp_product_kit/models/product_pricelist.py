# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(
        self,
        products,
        quantity,
        *,
        currency=None,
        uom=None,
        date=False,
        compute_price=True,
        **kwargs,
    ):
        res = super()._compute_price_rule(
            products,
            quantity,
            currency=currency,
            uom=uom,
            date=date,
            compute_price=compute_price,
            **kwargs,
        )
        if not compute_price:
            return res
        for product in products:
            if product._name == "product.product" and product.kit_product_ids:
                new_price = 0
                product_uom = product.uom_id
                target_uom = uom or product_uom
                if target_uom != product_uom:
                    qty_in_product_uom = target_uom._compute_quantity(
                        quantity, product_uom, raise_if_failure=False
                    )
                else:
                    qty_in_product_uom = quantity
                for kit_line in product.kit_product_ids:
                    line_qty = qty_in_product_uom * kit_line.product_qty
                    kit_price = self._compute_price_rule(
                        kit_line.component_product_id,
                        line_qty,
                        currency=currency,
                        uom=kit_line.component_product_id.uom_id,
                        date=date,
                        **kwargs,
                    )[kit_line.component_product_id.id]
                    new_price += kit_price[0] * line_qty
                res[product.id] = (new_price, False)
        return res
