# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


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
    product_qty = fields.Float("Quantity", default=1.0, required=True)
    product_price = fields.Float(compute="_compute_product_price", store=True)
    product_uom_id = fields.Many2one(
        related="component_product_id.uom_id", index=True, store=True
    )

    @api.constrains("product_qty")
    def _check_product_qty(self):
        for kit_line in self:
            if kit_line.product_qty <= 0:
                raise ValidationError(
                    self.env._(
                        "The quantity of component %(component)s in kit %(kit)s "
                        "must be greater than zero.",
                        component=kit_line.component_product_id.display_name,
                        kit=kit_line.product_id.display_name,
                    )
                )

    @api.constrains("product_id", "component_product_id")
    def _check_no_cycle(self):
        for kit_line in self:
            kit = kit_line.product_id
            # walk down from the component: reaching the kit again is a cycle
            seen = self.env["product.product"]
            todo = kit_line.component_product_id
            while todo:
                if kit in todo:
                    raise ValidationError(
                        self.env._(
                            "Kit %(kit)s cannot contain itself, directly or "
                            "through one of its components.",
                            kit=kit.display_name,
                        )
                    )
                seen |= todo
                todo = todo.kit_product_ids.component_product_id - seen

    @api.depends("product_id.display_name", "component_product_id.name")
    def _compute_display_name(self):
        for kit_line in self.sudo():
            kit_line.display_name = (
                f"{kit_line.product_id.display_name}"
                f" - {kit_line.component_product_id.name}"
            )

    # The component's own sales price has to be in here, otherwise the stored
    # value stays at what it was when the line was written and the kit keeps
    # selling at yesterday's price.
    @api.depends("component_product_id.lst_price", "product_qty")
    def _compute_product_price(self):
        for kit_line in self:
            kit_line.product_price = (
                kit_line.product_qty * kit_line.component_product_id.lst_price
            )
