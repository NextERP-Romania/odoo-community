# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    delivery_slip_report_only_name = fields.Boolean(
        related="company_id.delivery_slip_report_only_name",
        readonly=False,
    )

    delivery_slip_report_uom_precision = fields.Boolean(
        related="company_id.delivery_slip_report_uom_precision",
        readonly=False,
    )
    picking_report_lang_company = fields.Boolean(
        related="company_id.picking_report_lang_company",
        readonly=False,
    )
