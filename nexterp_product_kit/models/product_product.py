# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

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

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        # TDE FIXME: delegate to template or not ? fields are reencoded here ...
        # compatibility about context keys used a bit everywhere in the code
        kits = self.filtered(lambda l: l.kit_product_ids)
        no_kits = self - kits
        if kits:
            if not uom and self._context.get('uom'):
                uom = self.env['uom.uom'].browse(self._context['uom'])
            if not currency and self._context.get('currency'):
                currency = self.env['res.currency'].browse(self._context['currency'])

            products = self
            if price_type == 'standard_price':
                # standard_price field can only be seen by users in base.group_user
                # Thus, in order to compute the sale price from the cost for users not in this group
                # We fetch the standard price as the superuser
                products = self.with_company(company or self.env.company).sudo()

            prices = dict.fromkeys(self.ids, 0.0)
            for product in products:
                if product.kit_product_ids:
                    prices[product.id] = sum(product.sudo().kit_product_ids.mapped('product_price')) or 0.0
                else:
                    prices[product.id] = product[price_type] or 0.0
                if price_type == 'list_price':
                    prices[product.id] += product.price_extra
                    # we need to add the price from the attributes that do not generate variants
                    # (see field product.attribute create_variant)
                    if self._context.get('no_variant_attributes_price_extra'):
                        # we have a list of price_extra that comes from the attribute values, we need to sum all that
                        prices[product.id] += sum(self._context.get('no_variant_attributes_price_extra'))

                if uom:
                    prices[product.id] = product.uom_id._compute_price(prices[product.id], uom)

                # Convert from current user company currency to asked one
                # This is right cause a field cannot be in more than one currency
                if currency:
                    prices[product.id] = product.currency_id._convert(
                        prices[product.id], currency, product.company_id, fields.Date.today())

            return prices
        else:
            return super(ProductProduct, no_kits).price_compute(price_type, uom, currency, company)
