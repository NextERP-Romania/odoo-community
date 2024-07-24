# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"
    _name = "account.invoice.report"

    is_inter_company = fields.Boolean(readonly=False)

    def _select(self):
        res = super()._select()
        select_str = res + """, move.is_inter_company AS is_inter_company """
        return select_str
