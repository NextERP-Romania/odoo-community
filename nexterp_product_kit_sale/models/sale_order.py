# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import api, fields, models
from odoo.exceptions import UserError


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

    def write(self, vals):
        if self._name == "sale.order.line" and {
            "product_id",
            "product_uom_id",
            "product_uom_qty",
        }.intersection(vals):
            for line in self.filtered(
                lambda line: line.kit_line_ids
                and line.order_id.state not in ("draft", "sent", "cancel")
            ):
                if (
                    vals.get("product_id", line.product_id.id) != line.product_id.id
                    or vals.get("product_uom_id", line.product_uom_id.id)
                    != line.product_uom_id.id
                    or line.product_uom_id.compare(
                        vals.get("product_uom_qty", line.product_uom_qty),
                        line.product_uom_qty,
                    )
                ):
                    raise UserError(
                        self.env._(
                            "The kit %(kit)s on confirmed order %(order)s cannot "
                            "change product, unit or quantity: its detail lines "
                            "would no longer match. Cancel the order and quote "
                            "the change again.",
                            kit=line.product_id.display_name,
                            order=line.order_id.name,
                        )
                    )
        return super().write(vals)

    def unlink(self):
        # sale.order.line.kit inherits this class; its own `kit_line_ids`
        # matches on ids of the other table and may point back at itself
        if self._name == "sale.order.line" and self.kit_line_ids:
            self.kit_line_ids.unlink()
        return super().unlink()

    def generate_sale_order_line_kit(self):
        for order_line in self:
            # Explicitly unlink old kit lines. Using `[(6, 0, [])]` on a
            # one2many only unrelates them (sale_line_id -> False) and leaves
            # the rows in the DB as orphans, which then accumulate every time
            # the parent SOL is edited.
            if order_line.kit_line_ids:
                order_line.kit_line_ids.sudo().unlink()
            if order_line.product_id.kit_product_ids:
                kit_lines_list = order_line._prepare_sale_kit_lines()
                order_line.kit_line_ids = [
                    (0, 0, kit_line_vals) for kit_line_vals in kit_lines_list
                ]
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
