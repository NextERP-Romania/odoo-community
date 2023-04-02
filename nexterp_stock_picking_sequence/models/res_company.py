# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    stock_assign_number_in_process = fields.Boolean(
        string="Assign Picking Number in Action Done"
    )

    draft_picking_sequence_id = fields.Many2one(
        "ir.sequence", string="Draft Picking Sequence"
    )
