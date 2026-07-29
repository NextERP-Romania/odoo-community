from odoo import api, fields, models

from .availability_status import STATUS_SELECTION


class StockPicking(models.Model):
    _inherit = "stock.picking"

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
        for picking in self:
            code, label, ratio = picking.move_ids._ne_aggregate_status()
            picking.availability_status_code = code
            picking.availability_status_label = label
            picking.availability_ratio = ratio
