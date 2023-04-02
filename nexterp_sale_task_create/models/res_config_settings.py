# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_create_taks_auto = fields.Boolean(
        string="Auto Create Sale Tasks",
        related="company_id.sale_create_taks_auto",
        readonly=False,
    )
