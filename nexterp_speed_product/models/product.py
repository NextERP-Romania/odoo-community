# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_variant_count = fields.Integer(store=True, index=True)


class ProductProduct(models.Model):
    _inherit = "product.product"

    name = fields.Char(related="product_tmpl_id.name", store=True, index=True)
    product_variant_count = fields.Integer(store=True, index=True)


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    name = fields.Char(store=True, index=True)
    html_color = fields.Char(store=True, index=True)
    display_type = fields.Selection(store=True, index=True)
