# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from odoo import fields, models


class Pricelist(models.Model):
    _inherit = "product.pricelist"

    currency_id = fields.Many2one(index=True)
    company_id = fields.Many2one(index=True)


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    product_tmpl_id = fields.Many2one(index=True)
    product_id = fields.Many2one(index=True)
    categ_id = fields.Many2one(index=True)
    company_id = fields.Many2one(index=True)
    currency_id = fields.Many2one(index=True)
    name = fields.Char(store=True, index=True)
    price = fields.Char(store=True, index=True)
