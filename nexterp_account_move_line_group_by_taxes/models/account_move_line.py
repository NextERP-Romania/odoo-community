# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_names = fields.Char(compute="_compute_tax_names", readonly=True, store=True)

    def _compute_tax_names(self):
        for line in self:
            tax_names = ""
            for tax in line.tax_ids:
                tax_names += tax.name + ", "
            line.tax_names = tax_names[:-2]
