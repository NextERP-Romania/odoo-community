# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models



class PickingType(models.Model):
    _inherit = "stock.picking.type"

    warehouse_id = fields.Many2one(index=True)
