# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    variant_seller_ids = fields.One2many("product.supplierinfo", "product_id")


class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    name = fields.Many2one(index=True)
    sequence = fields.Integer(index=True)
    currency_id = fields.Many2one(index=True)
    date_start = fields.Date(index=True)
    date_end = fields.Date(index=True)
    product_id = fields.Many2one(index=True)
    product_name = fields.Char(index=True)
    product_code = fields.Char(index=True)
    product_uom = fields.Many2one(index=True)
