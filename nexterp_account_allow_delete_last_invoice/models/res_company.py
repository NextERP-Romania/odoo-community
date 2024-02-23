# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_allow_delete_last_invoice = fields.Boolean(
        string="Allow Delete Last Invoice"
    )
