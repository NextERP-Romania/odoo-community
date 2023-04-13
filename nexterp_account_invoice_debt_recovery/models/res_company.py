# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_allow_debt_recovery_invoice = fields.Boolean(
        string="Allow Debt Recovery on Invoice"
    )
