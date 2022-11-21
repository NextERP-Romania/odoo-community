# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    account_allow_debt_recovery_invoice = fields.Boolean(
        related="company_id.account_allow_debt_recovery_invoice",
        readonly=False,
    )
