# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from odoo import fields, models


class StockWarehouseOrderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    warehouse_id = fields.Many2one(index=True)
    group_id = fields.Many2one(index=True)
    route_id = fields.Many2one(index=True)
