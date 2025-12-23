# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import math

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "uom.uom"

    report_precision = fields.Integer(
        string="Report Precision",
        help="Number of decimal places to use in reports for this unit of measure.",
        compute="_compute_report_precision",
        store=True,
        readonly=False,
    )

    @api.depends("rounding")
    def _compute_report_precision(self):
        for uom in self:
            uom.report_precision = uom.rounding and int(-math.log10(uom.rounding)) or 0
