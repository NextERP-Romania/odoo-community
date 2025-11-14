# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/18.0/legal/licenses/licenses.html#).

from odoo import api, fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"
    _name = "account.invoice.report"

    is_inter_company = fields.Boolean(readonly=False)

    @api.model
    def _select(self) -> SQL:
        return SQL("%s, move.is_inter_company AS is_inter_company", super()._select())
