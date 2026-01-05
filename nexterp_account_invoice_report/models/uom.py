# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    report_precision = fields.Integer(
        help="Number of decimal places to use in reports for this unit of measure.",
    )
