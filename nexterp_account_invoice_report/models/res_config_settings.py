# Copyright 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    print_show_refunds = fields.Boolean(
        related="company_id.print_show_refunds",
        readonly=False,
    )

    print_invoice_tax_value = fields.Boolean(
        related="company_id.print_invoice_tax_value",
        readonly=False,
    )

    print_invoice_total_value = fields.Boolean(
        related="company_id.print_invoice_total_value",
        readonly=False,
    )
