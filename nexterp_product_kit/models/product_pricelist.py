# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import models
from odoo.exceptions import UserError


class ProductPircelist(models.Model):
    _inherit = "product.pricelist"

    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):
        """Low-level method - Mono pricelist, multi products
        Returns: dict{product_id: (price, suitable_rule) for the given pricelist}

        Date in context can be a date, datetime, ...

            :param products_qty_partner: list of typles products, quantity, partner
            :param datetime date: validity date
            :param ID uom_id: intermediate unit of measure
        """
        self.ensure_one()
        if not uom_id and self._context.get("uom"):
            uom_id = self._context["uom"]
        if uom_id:
            # rebrowse with uom if given
            products = [
                item[0].with_context(uom=uom_id) for item in products_qty_partner
            ]
            products_qty_partner = [
                (products[index], data_struct[1], data_struct[2])
                for index, data_struct in enumerate(products_qty_partner)
            ]
        res = super()._compute_price_rule(products_qty_partner, date, uom_id)
        for product, qty, partner in products_qty_partner:
            if product._name == "product.product" and product.kit_product_ids:
                new_price = 0
                for kit_line in product.kit_product_ids:
                    qty_uom_id = self._context.get("uom") or product.uom_id.id
                    qty_in_product_uom = qty
                    if qty_uom_id != product.uom_id.id:
                        try:
                            qty_in_product_uom = (
                                self.env["uom.uom"]
                                .browse([self._context["uom"]])
                                ._compute_quantity(qty, product.uom_id)
                            )
                        except UserError:
                            # Ignored - incompatible UoM in context, use default product UoM
                            pass
                    quantity = qty_in_product_uom * kit_line.product_qty
                    kit_price = self._compute_price_rule(
                        [(kit_line.component_product_id, quantity, partner)],
                        date,
                        uom_id,
                    )[kit_line.component_product_id.id]
                    new_price += kit_price[0] * quantity
                res[product.id] = (new_price, False)
        return res
