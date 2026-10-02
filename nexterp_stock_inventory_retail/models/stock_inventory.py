# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from collections import defaultdict

from odoo import api, fields, models


class StockInventory(models.Model):
    _inherit = "l10n.ro.stock.inventory"

    l10n_ro_retail_markup_value = fields.Monetary(
        string="Markup Difference (378)",
        compute="_compute_l10n_ro_retail_values",
        help="Net value the inventory differences put on, or take off, the "
        "commercial markup account.",
    )
    l10n_ro_retail_vat_value = fields.Monetary(
        string="Deferred VAT Difference (4428)",
        compute="_compute_l10n_ro_retail_values",
        help="Net value the inventory differences put on, or take off, the "
        "deferred VAT account.",
    )
    l10n_ro_retail_value = fields.Monetary(
        string="Retail Difference (371)",
        compute="_compute_l10n_ro_retail_values",
        help="Net value of the differences at shelf price: the cost "
        "difference plus the markup and the deferred VAT that go with it.",
    )

    @api.depends(
        "inventory_line_ids.l10n_ro_retail_markup_value",
        "inventory_line_ids.l10n_ro_retail_vat_value",
        "inventory_line_ids.l10n_ro_retail_value",
    )
    def _compute_l10n_ro_retail_values(self):
        for inventory in self:
            lines = inventory.inventory_line_ids
            inventory.l10n_ro_retail_markup_value = sum(
                lines.mapped("l10n_ro_retail_markup_value")
            )
            inventory.l10n_ro_retail_vat_value = sum(
                lines.mapped("l10n_ro_retail_vat_value")
            )
            inventory.l10n_ro_retail_value = sum(lines.mapped("l10n_ro_retail_value"))

    def _l10n_ro_retail_report_lines(self):
        """The printed lines that sit in a shop, in the order they print.

        The retail section of the inventory report only concerns goods carried
        at shelf price; a company counting both a warehouse and a shop in one
        document gets the section for the shop alone.
        """
        self.ensure_one()
        return self._report_lines().filtered(
            lambda line: line.location_id.l10n_ro_retail
        )


class StockInventoryLine(models.Model):
    _inherit = "l10n.ro.stock.inventory.line"

    l10n_ro_retail_price = fields.Monetary(
        string="Shelf Price",
        compute="_compute_l10n_ro_retail_price",
        help="Shelf price (PVA, VAT included) the shop currently charges for "
        "one unit of this product.",
    )
    l10n_ro_retail_markup_value = fields.Monetary(
        string="Markup (378)",
        readonly=True,
        help="Share of the difference that lands on the commercial markup "
        "account, filled together with the cost difference.",
    )
    l10n_ro_retail_vat_value = fields.Monetary(
        string="Deferred VAT (4428)",
        readonly=True,
        help="Share of the difference that lands on the deferred VAT "
        "account, filled together with the cost difference.",
    )
    l10n_ro_retail_value = fields.Monetary(
        string="Retail Value (371)",
        compute="_compute_l10n_ro_retail_value",
        store=True,
        help="Difference at shelf price: the cost difference plus the markup "
        "and the deferred VAT that go with it - what account 371 moves by.",
    )

    @api.depends(
        "inventory_diff_value",
        "l10n_ro_retail_markup_value",
        "l10n_ro_retail_vat_value",
    )
    def _compute_l10n_ro_retail_value(self):
        for line in self:
            line.l10n_ro_retail_value = (
                line.inventory_diff_value
                + line.l10n_ro_retail_markup_value
                + line.l10n_ro_retail_vat_value
            )

    @api.depends("product_id", "location_id")
    def _compute_l10n_ro_retail_price(self):
        self.l10n_ro_retail_price = 0.0
        lines_by_warehouse = defaultdict(lambda: self.browse())
        for line in self:
            warehouse = line.location_id.warehouse_id
            if line.location_id.l10n_ro_retail and warehouse:
                lines_by_warehouse[warehouse] |= line
        for warehouse, lines in lines_by_warehouse.items():
            # The pricelist is read once per shop: an inventory covering a
            # whole shop would otherwise search the price rules once per
            # article.
            prices = lines.product_id._l10n_ro_get_retail_prices_batch(
                warehouse=warehouse, company=warehouse.company_id
            )
            for line in lines:
                price = prices.get(line.product_id.id)
                if price:
                    line.l10n_ro_retail_price = price["price_with_vat"]

    def _update_diff_values(self):
        """Value the markup and the deferred VAT alongside the cost."""
        res = super()._update_diff_values()
        for line in self:
            markup, vat = line._l10n_ro_retail_diff_amounts()
            line.l10n_ro_retail_markup_value = markup
            line.l10n_ro_retail_vat_value = vat
        return res

    def _report_diff_value(self):
        """Goods held in a shop are counted at shelf price.

        That is what account 371 carries for them and what the shop answers
        for, so the whole document - the per-location summary, the
        differences and their totals - is drawn at the PVA rather than at
        cost. The split into cost, markup and deferred VAT is printed by the
        retail section underneath.
        """
        self.ensure_one()
        if self.location_id.l10n_ro_retail:
            return self.l10n_ro_retail_value
        return super()._report_diff_value()

    def _l10n_ro_retail_diff_amounts(self):
        """Markup and deferred VAT the counted difference will book.

        This mirrors what the adjustment move does in
        `l10n_ro_stock_account_retail`: a surplus is loaded from the shelf
        price the shop charges today, a shortage releases what the markup
        ledger carries, prorated over the quantity carrying it. Reading the
        ledger rather than the pricelist for a shortage is what makes the
        report agree with accounts 378 and 4428 - the goods may have been
        taken in at a price the shop has since changed.
        """
        self.ensure_one()
        location = self.location_id
        warehouse = location.warehouse_id
        quantity = self.inventory_diff_quantity
        if not quantity or not warehouse or not location.l10n_ro_retail:
            return 0.0, 0.0
        company = self.company_id or self.env.company
        currency = company.currency_id
        product = self.product_id
        if quantity > 0:
            prices = product._l10n_ro_get_retail_prices_batch(
                warehouse=warehouse, company=company
            ).get(product.id)
            if not prices:
                # No rule on the shop's retail pricelist: the move would
                # refuse the goods, and the report says nothing rather than
                # inventing a markup.
                return 0.0, 0.0
            cost_unit = self.inventory_diff_value / quantity
            markup = (prices["price_without_vat"] - cost_unit) * quantity
            return currency.round(markup), currency.round(prices["vat"] * quantity)
        ledger = self.env["l10n.ro.retail.markup.line"]
        qty_before, _cost, markup, vat = ledger._l10n_ro_balance(
            warehouse, product, company
        )
        if currency.is_zero(markup) and currency.is_zero(vat):
            return 0.0, 0.0
        out_qty = -quantity
        if product.uom_id.compare(qty_before, out_qty) <= 0:
            # The ledger carries no more than what is missing, so both
            # accounts close.
            return -markup, -vat
        ratio = out_qty / qty_before
        return currency.round(-markup * ratio), currency.round(-vat * ratio)
