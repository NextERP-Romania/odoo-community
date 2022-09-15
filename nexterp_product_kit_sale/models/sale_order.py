# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    kit_line_ids = fields.One2many(
        "sale.order.line.kit", "order_id", "Kit Sale Lines", copy=False
    )


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    kit_line_ids = fields.One2many(
        "sale.order.line.kit", "sale_line_id", "Kit Sale Lines", copy=False
    )

    def generate_sale_order_line_kit(self):
        for order_line in self:
            if order_line.kit_line_ids:
                order_line.kit_line_ids = [(6, 0, [])]
            if order_line.product_id.kit_product_ids:
                kit_lines_list = order_line._prepare_sale_kit_lines()
                input_line_vals = [
                    (0, 0, kit_line_vals) for kit_line_vals in kit_lines_list
                ]
            order_line.kit_line_ids = input_line_vals

    def _prepare_sale_kit_lines(self):
        self.ensure_one()
        vals_list = []
        for kit_line in self.product_id.kit_product_ids:
            res = self.env["sale.order.line.kit"]._prepare_sale_order_line_data(
                kit_line, self
            )
            vals_list.append(res)
        return vals_list

    def get_to_generate_fields(self):
        return ["product_id", "product_uom_qty", "product_uom", "discount"]

    def write(self, vals):
        res = super().write(vals)
        dependable_fields = self.get_to_generate_fields()
        should_regenerate = False
        for key in list(vals):
            if key in dependable_fields:
                should_regenerate = True
                break
        if (
            should_regenerate
            and self._name == "sale.order.line"
            and not self.env.context.get("change_from_soline")
        ):
            self.with_context(change_from_soline=True).generate_sale_order_line_kit()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        if self._name == "sale.order.line" and not self.env.context.get(
            "change_from_soline"
        ):
            res.with_context(change_from_soline=True).generate_sale_order_line_kit()
        return res
