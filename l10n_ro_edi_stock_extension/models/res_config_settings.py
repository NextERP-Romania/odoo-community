# Copyright 2026 NextERP Romania SRL
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_ro_edi_stock_default_price_source = fields.Selection(
        related="company_id.l10n_ro_edi_stock_default_price_source",
        readonly=False,
    )
    l10n_ro_edi_stock_list_days = fields.Integer(
        related="company_id.l10n_ro_edi_stock_list_days",
        readonly=False,
    )
    l10n_ro_edi_stock_list_enabled = fields.Boolean(
        related="company_id.l10n_ro_edi_stock_list_enabled",
        readonly=False,
    )
