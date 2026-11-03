# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_ro_create_customer_autoinvoice = fields.Boolean(
        string="Create Customer Self-Invoices",
        help="Take in from the SPV, as customer invoices, the self-invoices "
        "customers issue in the company's name.",
    )
