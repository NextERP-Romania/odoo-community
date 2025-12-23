# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    delivery_slip_report_only_name = fields.Boolean()
    delivery_slip_report_uom_precision = fields.Boolean()
    picking_report_lang_company = fields.Boolean()
