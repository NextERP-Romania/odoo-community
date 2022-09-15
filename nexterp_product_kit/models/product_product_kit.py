# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ProductKit(models.Model):
    _name = "product.product.kit"
    _description = "Product Kits"

    product_id = fields.Many2one(
        "product.product", string="Product", required=True, index=True
    )
    categ_id = fields.Many2one(related="product_id.categ_id", store=True, index=True)
    component_product_id = fields.Many2one(
        "product.product", string="Component Product", required=True, index=True
    )
    product_qty = fields.Float(
        "Quantity", default=1.0, digits="Product Unit of Measure", required=True
    )
    product_uom_id = fields.Many2one(
        related="component_product_id.uom_id", index=True, store=True
    )

    def name_get(self):
        result = []
        for kit_line in self.sudo():
            name = "%s - %s" % (
                kit_line.product_id.name_get()[0][1],
                kit_line.component_product_id.name,
            )
            result.append((kit_line.id, name))
        return result
