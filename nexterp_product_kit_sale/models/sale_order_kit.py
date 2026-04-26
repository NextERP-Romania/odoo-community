# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import api, fields, models
from odoo.tools.misc import get_lang


class SaleOrderLineKit(models.Model):
    _name = "sale.order.line.kit"
    _inherit = "sale.order.line"
    _description = "Sale Order Line kit"

    sale_line_id = fields.Many2one("sale.order.line", "Sale Order Line")
    invoice_lines = fields.Many2many(
        "account.move.line",
        "sale_order_detail_line_invoice_rel",
        "order_line_id",
        "invoice_line_id",
        copy=False,
    )
    product_document_ids = fields.Many2many(
        "product.document",
        "sale_order_line_kit_product_document_rel",
        "sale_order_line_kit_id",
        "product_document_id",
    )

    @api.model
    def _prepare_sale_order_line_data(self, kit_line, line):
        """Generate the Sales Order Line Kit values from the SO line
        :param kit_line : the origin sale order kit line
        :rtype kit_line : sale.order.line.kit record
        :param line : the origin Sale Order Line
        :rtype line : sale.order.line record
        """
        order = line.order_id or line._origin.order_id
        lang = get_lang(self.env, order.partner_id.lang).code
        quantity = line.product_uom_id._compute_quantity(
            line.product_uom_qty, line.product_id.uom_id
        )
        quantity = quantity * kit_line.product_qty
        product = kit_line.component_product_id.with_context(
            lang=lang,
            partner=order.partner_id,
            quantity=quantity,
            date=order.date_order,
            pricelist=order.pricelist_id.id,
            uom=kit_line.product_uom_id.id,
        )
        vals = self._add_missing_default_values({})
        vals.update(
            {
                "product_id": product.id,
                "product_uom_qty": quantity,
                "product_uom_id": kit_line.product_uom_id.id,
                "order_id": order.id or order._origin.id,
                "tax_ids": line.tax_ids or line._origin.tax_ids,
            }
        )
        if line.id or line._origin.id:
            vals.update({"sale_line_id": line.id or line._origin.id})

        if order.pricelist_id and order.partner_id:
            # Take the unit price from the component product's pricelist
            # entry, NOT from the parent SO line (which is the kit-as-a-whole
            # price). `product` is already wrapped with the pricelist /
            # partner / quantity / uom / date context above, so
            # `_get_contextual_price()` returns the correct unit price for
            # this kit component.
            component_price = product.with_company(
                line.company_id
            )._get_contextual_price()
            vals["price_unit"] = product._get_tax_included_unit_price(
                line.company_id,
                order.currency_id,
                order.date_order,
                "sale",
                fiscal_position=order.fiscal_position_id,
                product_price_unit=component_price,
                product_currency=order.currency_id,
            )
        taxes = line.tax_ids.compute_all(
            vals["price_unit"],
            order.currency_id,
            quantity,
            product=product,
            partner=order.partner_shipping_id,
        )
        vals.update(
            {
                "price_tax": sum(t.get("amount", 0.0) for t in taxes.get("taxes", [])),
                "price_total": taxes["total_included"],
                "price_subtotal": taxes["total_excluded"],
            }
        )
        return vals

    _RECOMPUTE_PARENT_PRICE_FIELDS = (
        "product_uom_qty",
        "price_unit",
        "product_id",
        "tax_ids",
    )

    def write(self, vals):
        res = super().write(vals)
        # Recompute parent SO line price only when relevant fields changed
        # AND we are not already inside a parent-driven change.
        if not self.env.context.get("change_from_soline") and any(
            field in vals for field in self._RECOMPUTE_PARENT_PRICE_FIELDS
        ):
            sale_lines = self.mapped("sale_line_id")
            sale_lines = sale_lines.with_context(change_from_soline=True)
            for line in sale_lines:
                line.price_unit = self.get_sale_kit_price(line, line.kit_line_ids)
        # Drop orphan kit lines on the orders involved in this write.
        # Runs unconditionally (even under `change_from_soline`) because
        # `generate_sale_order_line_kit` clears kit_line_ids via `(6, 0, [])`,
        # which leaves the previous rows orphaned (sale_line_id=False) and
        # they need to be unlinked here. Scoped to the touched orders so
        # unrelated SOs are not swept.
        order_ids = self.mapped("order_id").ids
        if order_ids:
            orphan_lines = self.search(
                [
                    ("order_id", "in", order_ids),
                    ("sale_line_id", "=", False),
                ]
            )
            if orphan_lines:
                orphan_lines.sudo().unlink()
        return res

    @api.model
    def get_sale_kit_price(self, sale_line, sale_kit_lines):
        domain = [("id", "in", sale_kit_lines.ids)]
        detail_lines = self.env["sale.order.line.kit"]._read_group(
            domain, ["sale_line_id"], ["price_subtotal:sum"]
        )
        sale_data = {sale_line.id: subtotal for sale_line, subtotal in detail_lines}
        if sale_line.product_uom_qty:
            price_unit = sale_data.get(sale_line.id, 0) / sale_line.product_uom_qty
        else:
            price_unit = 0
        return price_unit

    def _check_line_unlink(self):
        if self._name == "sale.order.line.kit":
            return self.browse()
        return super()._check_line_unlink()
