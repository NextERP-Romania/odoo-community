from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero

from .availability_status import STATUS_SELECTION, STATUS_SEVERITY


class StockMove(models.Model):
    _inherit = "stock.move"

    availability_status_code = fields.Selection(
        STATUS_SELECTION,
        string="Availability Status",
        compute="_compute_availability_status",
        compute_sudo=True,
    )
    availability_status_label = fields.Char(
        string="Availability Status Label",
        compute="_compute_availability_status",
        compute_sudo=True,
    )
    availability_ratio = fields.Float(
        string="Availability Ratio",
        compute="_compute_availability_status",
        compute_sudo=True,
    )

    # ------------------------------------------------------------------
    # Main compute
    # ------------------------------------------------------------------
    @api.depends("state", "product_uom_qty", "quantity", "product_qty",
                 "move_orig_ids", "move_orig_ids.state", "date", "date_deadline")
    def _compute_availability_status(self):
        today = fields.Date.context_today(self)
        # defaults
        self.availability_status_code = "none"
        self.availability_status_label = False
        self.availability_ratio = 0.0

        relevant = self.filtered(
            lambda m: m.state not in ("cancel", "draft") and m._is_consuming()
        )
        needs = self.browse()
        for move in relevant:
            demand = move.product_uom_qty
            rounding = move.product_id.uom_id.rounding or 0.01
            if float_is_zero(demand, precision_rounding=rounding):
                continue  # nothing to move on this line -> no light
            if move.state in ("done", "assigned"):
                move.availability_status_code = "available"
                move.availability_status_label = _("Available")
                move.availability_ratio = 1.0
            elif move.state == "partially_available":
                move.availability_status_code = "partial"
                move.availability_status_label = _("Partially available")
                move.availability_ratio = min(move.quantity / demand, 1.0) if demand else 0.0
            else:  # waiting / confirmed -> trace the supply
                needs |= move
        if needs:
            needs._ne_fill_supply_status(today)

    # ------------------------------------------------------------------
    # Supply tracing
    # ------------------------------------------------------------------
    def _ne_fill_supply_status(self, today):
        """For each not-available demand move, find where the replenishment is."""
        no_chain = self.browse()
        for move in self:
            supply = move.move_orig_ids.filtered(
                lambda m: m.state not in ("done", "cancel")
            )[:1]
            if supply:
                code, label = move._ne_classify_supply_move(supply, today)
                move.availability_status_code = code
                move.availability_status_label = label
            else:
                no_chain |= move
        if no_chain:
            no_chain._ne_infer_supply_status(today)

    def _ne_classify_supply_move(self, supply, today):
        """Classify a linked supply move (MTO / procurement chain)."""
        self.ensure_one()
        need = self.date_deadline or self.date
        if supply.purchase_line_id:
            return supply.purchase_line_id._ne_po_line_status(today, need)
        if supply.production_id:
            return supply.production_id._ne_mo_status(today, need)
        expected = supply.date_deadline or supply.date
        if supply.picking_id.picking_type_id.code == "internal":
            return self._ne_date_status("transfer", expected, need, today)
        return self._ne_date_status("reception", expected, need, today)

    def _ne_infer_supply_status(self, today):
        """No linked supply (MTS): infer from stock elsewhere / product route."""
        products = self.product_id
        # Batch: free stock (on hand - reserved) per product across the company.
        free_by_product = {
            p.id: p.free_qty for p in products
        }
        # Batch: earliest open PO line per product.
        po_by_product = {}
        pols = self.env["purchase.order.line"].search(
            [("product_id", "in", products.ids),
             ("order_id.state", "in", ("draft", "sent", "to approve", "purchase"))],
            order="date_planned asc",
        )
        for pol in pols:
            po_by_product.setdefault(pol.product_id.id, pol)
        # Batch: earliest open MO per product.
        mo_by_product = {}
        mos = self.env["mrp.production"].search(
            [("product_id", "in", products.ids),
             ("state", "not in", ("done", "cancel"))],
            order="date_start asc",
        )
        for mo in mos:
            mo_by_product.setdefault(mo.product_id.id, mo)

        buy_route = self.env.ref("purchase_stock.route_warehouse0_buy", raise_if_not_found=False)
        mfg_route = self.env.ref("mrp.route_warehouse0_manufacture", raise_if_not_found=False)

        for move in self:
            product = move.product_id
            need = move.date_deadline or move.date
            rounding = product.uom_id.rounding or 0.01
            # 1. Stock available somewhere else -> an internal transfer can fill it.
            if not float_is_zero(free_by_product.get(product.id, 0.0), precision_rounding=rounding):
                move.availability_status_code = "to_transfer"
                move.availability_status_label = _("Internal transfer needed")
                continue
            # 2. Route-based.
            routes = product.route_ids
            is_manufacture = bool(product.bom_ids) and (not mfg_route or mfg_route in routes)
            is_buy = buy_route and buy_route in routes
            if is_manufacture and not (is_buy and product.id in po_by_product):
                mo = mo_by_product.get(product.id)
                if mo:
                    code, label = mo._ne_mo_status(today, need)
                else:
                    code, label = "to_manufacture", _("Must be manufactured")
            else:
                pol = po_by_product.get(product.id)
                if pol:
                    code, label = pol._ne_po_line_status(today, need)
                else:
                    code, label = "to_order", _("Must be ordered")
            move.availability_status_code = code
            move.availability_status_label = label

    # ------------------------------------------------------------------
    # Date helpers
    # ------------------------------------------------------------------
    def _ne_date_status(self, kind, expected, need, today):
        """Build (code, label) for a date-driven supply (reception/transfer)."""
        late_code = {"reception": "reception_late", "transfer": "transfer_late"}[kind]
        ok_code = kind
        if self._ne_is_late(expected, need, today):
            label = {"reception": _("Reception is late"),
                     "transfer": _("Transfer is late")}[kind]
            return late_code, label
        days = self._ne_days(expected, today)
        if kind == "reception":
            label = _("Reception today") if days <= 0 else _("Reception in %s days", days)
        else:
            label = _("Transfer today") if days <= 0 else _("Transfer in %s days", days)
        return ok_code, label

    @staticmethod
    def _ne_to_date(value):
        if not value:
            return False
        return value.date() if hasattr(value, "date") else value

    @api.model
    def _ne_is_late(self, expected, need, today):
        exp = self._ne_to_date(expected)
        if not exp:
            return False
        if exp < today:
            return True
        need_d = self._ne_to_date(need)
        return bool(need_d and exp > need_d)

    @api.model
    def _ne_days(self, expected, today):
        exp = self._ne_to_date(expected)
        if not exp:
            return 0
        return max((exp - today).days, 0)

    # ------------------------------------------------------------------
    # Aggregation helper (used by picking / MO / sale line)
    # ------------------------------------------------------------------
    def _ne_aggregate_status(self):
        """Roll several moves into one (code, label, ratio): the worst line wins."""
        moves = self.filtered(lambda m: m.availability_status_code not in (False, "none"))
        if not moves:
            return "none", False, 0.0
        worst = max(moves, key=lambda m: STATUS_SEVERITY.get(m.availability_status_code, 0))
        ratio = sum(moves.mapped("availability_ratio")) / len(moves)
        return worst.availability_status_code, worst.availability_status_label, ratio
