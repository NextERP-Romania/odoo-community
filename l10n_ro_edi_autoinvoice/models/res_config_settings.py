# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_ro_create_customer_autoinvoice = fields.Boolean(
        related="company_id.l10n_ro_create_customer_autoinvoice",
        readonly=False,
    )
