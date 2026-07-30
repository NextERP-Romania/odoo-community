from odoo import models, _


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _ne_po_line_status(self, today, need):
        """Status of this PO line seen as a supply (reception) for a demand.

        Used by stock.move to classify purchased components; the purchase order
        line itself no longer displays a traffic-light column.
        """
        self.ensure_one()
        if self.order_id.state in ("draft", "sent", "to approve"):
            return "po_draft", _("Purchase not validated")
        return "reception", _("Reception needed")
