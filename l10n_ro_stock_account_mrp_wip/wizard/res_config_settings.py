# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _name = "res.config.settings"
    _inherit = ["res.config.settings", "l10n.ro.mixin"]

    account_production_wip_account_id = fields.Many2one(
        "account.account",
        related="company_id.account_production_wip_account_id",
        readonly=False,
    )

    account_production_wip_overhead_account_id = fields.Many2one(
        "account.account",
        related="company_id.account_production_wip_overhead_account_id",
        readonly=False,
    )
