# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stock_assign_number_in_process = fields.Boolean(
        related="company_id.stock_assign_number_in_process",
        readonly=False,
    )

    draft_picking_sequence_id = fields.Many2one(
        related="company_id.draft_picking_sequence_id", readonly=False
    )
