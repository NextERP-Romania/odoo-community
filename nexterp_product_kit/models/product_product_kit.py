# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class ProductKit(models.Model):
    _name = "product.product.kit"
    _description = "Product Kits"

    product_id = fields.Many2one(
        "product.product", string="Product", required=True, index=True
    )
    categ_id = fields.Many2one(related="product_id.categ_id", store=True, index=True)
    product_template_id = fields.Many2one(
        "product.template", related="product_id.product_tmpl_id", store=True, index=True
    )
    component_product_id = fields.Many2one(
        "product.product", string="Component Product", required=True, index=True
    )
    product_qty = fields.Float(
        "Quantity", default=1.0, digits="Product Unit of Measure", required=True
    )
    product_price = fields.Float(compute="_compute_product_price", store=True)
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

    @api.depends("component_product_id", "product_qty")
    def _compute_product_price(self):
        for kit_line in self:
            kit_line.product_price = (
                kit_line.product_qty * kit_line.component_product_id.lst_price
            )
