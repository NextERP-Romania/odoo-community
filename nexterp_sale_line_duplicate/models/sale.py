# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def action_duplicate(self):
        res_id = self.env["sale.order.line.duplicate"].create({"sale_line_id": self.id})
        return {
            "name": _("Duplicate Sales Order Line"),
            "view_mode": "form",
            "res_model": "sale.order.line.duplicate",
            "view_id": self.env.ref(
                "nexterp_sale_line_duplicate.sale_line_duplicate_view_form"
            ).id,
            "type": "ir.actions.act_window",
            "context": dict(self._context),
            "res_id": res_id.id,
            "target": "new",
        }
