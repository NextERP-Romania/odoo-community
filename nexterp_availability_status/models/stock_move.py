from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero

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
    @api.depends("state", "product_uom_qty", "quantity", "product_qty", "location_id",
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
        # Availability is about PHYSICAL STOCK EXISTING at the source, not about
        # this move being reserved: reservations can be re-shuffled between moves,
        # so what matters is that the on-hand quantity exists (reservations by
        # other moves are ignored). Stock sitting in a sub-location of the source
        # counts too - it is directly reservable - but we flag it so the user
        # knows it is not in the source location itself. On-hand is read per
        # (product, location, strict) and cached to stay a handful of queries.
        Quant = self.env["stock.quant"]
        onhand_cache = {}

        def on_hand(product, location, strict):
            key = (product.id, location.id, strict)
            if key not in onhand_cache:
                domain = [("product_id", "=", product.id)]
                domain.append(
                    ("location_id", "=", location.id) if strict
                    else ("location_id", "child_of", location.id)
                )
                quants = Quant.search(domain)
                onhand_cache[key] = sum(quants.mapped("quantity"))
            return onhand_cache[key]

        needs = self.browse()
        for move in relevant:
            product = move.product_id
            rounding = product.uom_id.rounding or 0.01
            demand_ref = move.product_qty  # product reference uom
            if float_is_zero(demand_ref, precision_rounding=rounding):
                continue  # nothing to move on this line -> no light
            if move.state == "done":
                move.availability_status_code = "available"
                move.availability_status_label = _("Available")
                move.availability_ratio = 1.0
                continue
            if product.type != "product":
                # Consumables / services do not hold stock -> always available.
                move.availability_status_code = "available"
                move.availability_status_label = _("Available")
                move.availability_ratio = 1.0
                continue
            here = on_hand(product, move.location_id, strict=True)   # source itself
            sub = on_hand(product, move.location_id, strict=False)   # incl. sub-locations
            if float_compare(here, demand_ref, precision_rounding=rounding) >= 0:
                move.availability_status_code = "available"
                move.availability_status_label = _("Available")
                move.availability_ratio = 1.0
            elif float_compare(sub, demand_ref, precision_rounding=rounding) >= 0:
                move.availability_status_code = "available_sub"
                move.availability_status_label = _("Available (sub-location)")
                move.availability_ratio = 1.0
            elif sub > 0:
                move.availability_status_code = "partial"
                move.availability_status_label = _("Partially available")
                move.availability_ratio = min(sub / demand_ref, 1.0)
            else:  # no physical stock anywhere under the source -> trace the supply
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
        """Classify a linked supply by walking the chain to its real origin.

        The immediate supply move may just be an internal step (e.g. input ->
        stock) whose real driver is a PO, an MO or a receipt further upstream, so
        we follow move_orig_ids until we hit something concrete. An internal
        transfer with no deeper origin stays a transfer.
        """
        self.ensure_one()
        need = self.date_deadline or self.date
        move = supply
        seen = set()
        fallback = None
        while move and move.id not in seen and len(seen) < 10:
            seen.add(move.id)
            if move.purchase_line_id:
                return move.purchase_line_id._ne_po_line_status(today, need)
            if move.production_id:
                return move.production_id._ne_mo_status(today, need)
            pt = move.picking_id.picking_type_id.code
            if pt == "incoming":
                return "reception", _("Reception needed")
            if pt == "internal":
                fallback = ("to_transfer", _("Internal transfer needed"))
            deeper = move.move_orig_ids.filtered(
                lambda m: m.state not in ("done", "cancel")
            )[:1]
            if not deeper:
                break
            move = deeper
        return fallback or ("reception", _("Reception needed"))

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
    # Date helpers (used to flag late production)
    # ------------------------------------------------------------------
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
