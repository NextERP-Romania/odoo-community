# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import fields, models

_logger = logging.getLogger("SFTP")


class SaleOrderLineDuplicate(models.TransientModel):
    _name = "sale.order.line.duplicate"
    _description = "Sale Order Line Duplicate Wizard"

    sale_line_id = fields.Many2one(
        "sale.order.line",
        string="Sale Order Line",
    )

    count = fields.Integer(string="Count", default=1)

    def action_duplicate(self):
        if self.count > 0:
            for _idx in range(self.count):
                self.sale_line_id.copy(default=self.get_copy_default_dict())

    def get_copy_default_dict(self):
        return {
            "order_id": self.sale_line_id.order_id.id,
        }
