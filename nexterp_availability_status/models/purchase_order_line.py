from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare

from .availability_status import STATUS_SELECTION


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

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

    @api.depends("order_id.state", "qty_received", "product_qty", "date_planned", "product_id")
    def _compute_ne_availability_status(self):
        today = fields.Date.context_today(self)
        for line in self:
            code, label, ratio = "none", False, 0.0
            product = line.product_id
            if not line.display_type and product and product.type in ("product", "consu"):
                rounding = product.uom_id.rounding or 0.01
                if float_compare(line.qty_received, line.product_qty, precision_rounding=rounding) >= 0:
                    code, label, ratio = "available", _("Received"), 1.0
                else:
                    code, label = line._ne_po_line_status(today, False)
            line.availability_status_code = code
            line.availability_status_label = label
            line.availability_ratio = ratio

    def _ne_po_line_status(self, today, need):
        """Status of this PO line seen as a supply (reception) for a demand."""
        self.ensure_one()
        if self.order_id.state in ("draft", "sent", "to approve"):
            return "po_draft", _("Purchase not validated")
        expected = self.date_planned
        move = self.env["stock.move"]
        if move._ne_is_late(expected, need, today):
            return "reception_late", _("Reception is late")
        days = move._ne_days(expected, today)
        label = _("Reception today") if days <= 0 else _("Reception in %s days", days)
        return "reception", label
