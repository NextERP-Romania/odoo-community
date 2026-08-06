from odoo import api, fields, models, _

from .availability_status import STATUS_SELECTION


class MrpProduction(models.Model):
    _inherit = "mrp.production"

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

    @api.depends("move_raw_ids.availability_status_code", "move_raw_ids.availability_ratio")
    def _compute_ne_availability_status(self):
        for production in self:
            code, label, ratio = production.move_raw_ids._ne_aggregate_status()
            production.availability_status_code = code
            production.availability_status_label = label
            production.availability_ratio = ratio

    def _ne_mo_status(self):
        """Status of this MO seen as a supply for a downstream demand."""
        self.ensure_one()
        if self.state == "draft":
            return "mo_draft", _("Manufacturing not confirmed")
        return "production", _("Manufacturing needed")
