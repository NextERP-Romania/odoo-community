from odoo import api, fields, models

from .availability_status import STATUS_SELECTION


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    availability_status_code = fields.Selection(
        STATUS_SELECTION, string="Availability Status",
        compute="_compute_ne_availability_status", compute_sudo=True,
    )
    availability_status_label = fields.Char(
        string="Availability Status Label",
        compute="_compute_ne_availability_status", compute_sudo=True,
    )
    availability_ratio = fields.Float(
        string="Availability Ratio",
        compute="_compute_ne_availability_status", compute_sudo=True,
    )

    @api.depends("move_ids.availability_status_code", "move_ids.availability_ratio")
    def _compute_ne_availability_status(self):
        for line in self:
            code, label, ratio = line.move_ids._ne_aggregate_status()
            line.availability_status_code = code
            line.availability_status_label = label
            line.availability_ratio = ratio
