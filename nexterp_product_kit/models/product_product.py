# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_kit_component = fields.Boolean()
    kit_product_ids = fields.One2many(
        "product.product.kit", "product_id", "Kit Products"
    )

    @api.onchange("is_kit_component")
    def _onchange_is_kit_component(self):
        if self.is_kit_component:
            self.sale_ok = False

    def price_compute(
        self, price_type, uom=False, currency=False, company=None, date=False
    ):
        prices = super().price_compute(price_type, uom, currency, company, date)
        kits = self.filtered(lambda pr_kits: pr_kits.kit_product_ids)
        if kits:
            company = company or self.env.company
            date = date or fields.Date.context_today(self)
            kits = kits.with_company(company)
            if price_type == "standard_price":
                kits = kits.sudo()

            for product in kits:
                price = 0
                for line in product.kit_product_ids:
                    line_price = line.component_product_id.price_compute(
                        price_type, uom, currency, company, date
                    )[line.component_product_id.id]
                    price += line_price * line.product_qty
                prices[product.id] = price
        return prices

    @api.depends(
        "list_price",
        "price_extra",
        "kit_product_ids.product_qty",
        "kit_product_ids.product_price",
    )
    def _compute_product_lst_price(self):
        res = super()._compute_product_lst_price()
        to_uom = None
        if "uom" in self._context:
            to_uom = self.env["uom.uom"].browse(self._context["uom"])
        kits = self.filtered(lambda pr_kits: pr_kits.kit_product_ids)
        if kits:
            for product in kits:
                price = 0
                for line in product.kit_product_ids:
                    if self.env.context.get("pricelist"):
                        pricelist = self.env["product.pricelist"].browse(
                            self.env.context["pricelist"]
                        )
                        line_price = line.component_product_id.price_compute(
                            "lst_price",
                            line.component_product_id.uom_id,
                            pricelist.currency_id,
                            self.env.company,
                            fields.Date.today(),
                        )[line.component_product_id.id]
                        price += line_price * line.product_qty
                    else:
                        price += line.product_price
                if to_uom:
                    list_price = product.uom_id._compute_price(price, to_uom)
                else:
                    list_price = price
                product.lst_price = list_price + product.price_extra
        return res
