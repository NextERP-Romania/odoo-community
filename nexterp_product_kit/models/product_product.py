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
