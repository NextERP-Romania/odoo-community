# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_ro_sale_down_payment_product_id = fields.Many2one(
        related="company_id.l10n_ro_sale_down_payment_product_id",
        readonly=False,
    )
