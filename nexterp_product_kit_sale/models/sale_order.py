# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    kit_line_ids = fields.One2many(
        "sale.order.line.kit", "order_id", "Kit Sale Lines", copy=False
    )

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("change_from_soline") and "order_line" in vals:
            for order in self.filtered(lambda o: o.state in ("draft", "sent")):
                order_lines = order.order_line.with_context(change_from_soline=True)
                order_lines.generate_sale_order_line_kit()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            if record.order_line and not self.env.context.get("change_from_soline"):
                lines = record.order_line.with_context(change_from_soline=True)
                lines.generate_sale_order_line_kit()
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    kit_line_ids = fields.One2many(
        "sale.order.line.kit", "sale_line_id", "Kit Sale Lines", copy=False
    )

    def unlink(self):
        if self.kit_line_ids:
            self.kit_line_ids.unlink()
        return super(SaleOrderLine, self).unlink()

    def generate_sale_order_line_kit(self):
        for order_line in self:
            input_line_vals = []
            if order_line.kit_line_ids:
                order_line.kit_line_ids = [(6, 0, [])]
            if order_line.product_id.kit_product_ids:
                kit_lines_list = order_line._prepare_sale_kit_lines()
                input_line_vals = [
                    (0, 0, kit_line_vals) for kit_line_vals in kit_lines_list
                ]
            order_line.kit_line_ids = input_line_vals
            if not self.env.context.get("change_from_soline"):
                order_line.price_unit = self.env[
                    "sale.order.line.kit"
                ].get_sale_kit_price(order_line, order_line.kit_line_ids)

    def _prepare_sale_kit_lines(self):
        self.ensure_one()
        vals_list = []
        for kit_line in self.product_id.kit_product_ids:
            res = self.env["sale.order.line.kit"]._prepare_sale_order_line_data(
                kit_line, self
            )
            vals_list.append(res)
        return vals_list
