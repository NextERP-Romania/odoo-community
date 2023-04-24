# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

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
        quantity = line.product_uom._compute_quantity(
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
                "product_uom": kit_line.product_uom_id.id,
                "order_id": order.id or order._origin.id,
                "tax_id": line.tax_id or line._origin.tax_id,
            }
        )
        if line.id or line._origin.id:
            vals.update({"sale_line_id": line.id or line._origin.id})
        # vals.update(
        #     name=self.with_context(
        #         lang=lang
        #     )._get_sale_order_line_multiline_description_sale(product)
        # )

        if order.pricelist_id and order.partner_id:
            vals["price_unit"] = product._get_tax_included_unit_price(
                line.company_id,
                order.currency_id,
                order.date_order,
                "sale",
                fiscal_position=order.fiscal_position_id,
                product_price_unit=line.with_company(
                    line.company_id
                )._get_display_price(),
                product_currency=order.currency_id,
            )
        taxes = line.tax_id.compute_all(
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

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("change_from_soline") and (
            "product_uom_qty" in vals or "price_unit" in vals
        ):
            sale_lines = self.mapped("sale_line_id")
            sale_lines = sale_lines.with_context(change_from_soline=True)
            for line in sale_lines:
                line.price_unit = self.get_sale_kit_price(line, line.kit_line_ids)
            # TODO - Check why we have lines without sale_line_id, could be from onchanges
            # that's why we remove them here
        not_linked = self.search([("sale_line_id", "=", False)])
        not_linked.sudo().unlink()
        return res

    @api.model
    def get_sale_kit_price(self, sale_line, sale_kit_lines):
        domain = [("id", "in", sale_kit_lines.ids)]
        detail_lines = self.env["sale.order.line.kit"].read_group(
            domain, ["sale_line_id", "price_subtotal"], ["sale_line_id"]
        )
        sale_data = {
            data["sale_line_id"][0]: data["price_subtotal"] for data in detail_lines
        }
        if sale_line.product_uom_qty:
            price_unit = sale_data.get(sale_line.id, 0) / sale_line.product_uom_qty
        else:
            price_unit = 0
        return price_unit

    def _check_line_unlink(self):
        if self._name == "sale.order.line.kit":
            return
        return super()._check_line_unlink()
