# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_auto_update_price = fields.Boolean(
        string="Auto Update Sales Prices",
        related="company_id.sale_auto_update_price",
        readonly=False,
    )
