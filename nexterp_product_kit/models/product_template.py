# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_kit_component = fields.Boolean(
        related="product_variant_ids.is_kit_component",
        readonly=False,
    )
    kit_product_ids = fields.One2many(
        related="product_variant_ids.kit_product_ids",
        readonly=False,
    )
