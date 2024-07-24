# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    account_allow_delete_last_invoice = fields.Boolean(
        related="company_id.account_allow_delete_last_invoice",
        readonly=False,
    )
