# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    picking_type_id = fields.Many2one(index=True)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_uom = fields.Many2one(index=True)
    product_id = fields.Many2one(index=True)
    state = fields.Selection(index=True)
    picking_type_id = fields.Many2one(index=True)
