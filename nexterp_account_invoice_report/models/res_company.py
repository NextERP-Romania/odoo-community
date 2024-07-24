# Copyright 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    print_show_refunds = fields.Boolean()
    print_invoice_tax_value = fields.Boolean()
    print_invoice_total_value = fields.Boolean()
