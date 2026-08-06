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
                 "move_orig_ids", "move_orig_ids.state")
    def _compute_availability_status(self):
        # defaults
        self.availability_status_code = "none"
        self.availability_status_label = False
        self.availability_ratio = 0.0

        relevant = self.filtered(
            lambda m: m.state not in ("cancel", "draft") and m._is_consuming()
        )
        # Availability is about PHYSICAL STOCK EXISTING, not about this move being
        # reserved (reservations can be re-shuffled). On-hand is read per
        # (product, location) and cached to stay a handful of queries.
        Quant = self.env["stock.quant"]
        onhand_cache = {}
        internal_cache = {}

        def on_hand(product, location, strict):
            key = (product.id, location.id, strict)
            if key not in onhand_cache:
                domain = [("product_id", "=", product.id)]
                domain.append(
                    ("location_id", "=", location.id) if strict
                    else ("location_id", "child_of", location.id)
                )
                onhand_cache[key] = sum(Quant.search(domain).mapped("quantity"))
            return onhand_cache[key]

        def total_internal(product):
            if product.id not in internal_cache:
                quants = Quant.search([
                    ("product_id", "=", product.id),
                    ("location_id.usage", "=", "internal"),
                ])
                internal_cache[product.id] = sum(quants.mapped("quantity"))
            return internal_cache[product.id]

        chained = self.browse()
        needs = self.browse()
        for move in relevant:
            product = move.product_id
            rounding = product.uom_id.rounding or 0.01
            demand_ref = move.product_qty  # product reference uom
            if float_is_zero(demand_ref, precision_rounding=rounding):
                continue  # nothing to move on this line -> no light
            if move.state in ("done", "assigned"):
                # completed or fully reserved -> available
                move._ne_set("available", _("Available"), 1.0)
                continue
            if product.type != "product":
                # Consumables / services do not hold stock -> always available.
                move._ne_set("available", _("Available"), 1.0)
                continue
            # 1. Reservation chain FIRST: a move linked to a specific supply
            #    (move_orig_ids) is fulfilled by THAT source, not by random stock.
            if move.move_orig_ids.filtered(lambda m: m.state not in ("done", "cancel")):
                chained |= move
                continue
            # 2. No chain -> physical on-hand under the source (incl. sub-locations).
            here = on_hand(product, move.location_id, strict=True)
            sub = on_hand(product, move.location_id, strict=False)
            if float_compare(here, demand_ref, precision_rounding=rounding) >= 0:
                move._ne_set("available", _("Available"), 1.0)
            elif float_compare(sub, demand_ref, precision_rounding=rounding) >= 0:
                move._ne_set("available_sub", _("Available (sub-location)"), 1.0)
            elif sub > 0:
                move._ne_set("partial", _("Partially available"), min(sub / demand_ref, 1.0))
            elif float_compare(total_internal(product) - sub, 0.0, precision_rounding=rounding) > 0:
                # 3. Stock exists in another (internal) location -> a transfer is
                #    needed, but none is linked yet.
                move._ne_set("must_transfer", _("Must be transfered"), 0.0)
            else:  # 4. No stock anywhere -> decide by route (buy / manufacture).
                needs |= move
        if chained:
            chained._ne_fill_supply_status()
        if needs:
            needs._ne_infer_supply_status()

    def _ne_set(self, code, label, ratio):
        self.availability_status_code = code
        self.availability_status_label = label
        self.availability_ratio = ratio

    # ------------------------------------------------------------------
    # Supply tracing (chain)
    # ------------------------------------------------------------------
    def _ne_fill_supply_status(self):
        """Classify moves that have an active reservation chain."""
        no_chain = self.browse()
        for move in self:
            supply = move.move_orig_ids.filtered(
                lambda m: m.state not in ("done", "cancel")
            )
            if supply:
                code, label = move._ne_classify_supply_move(supply)
                move._ne_set(code, label, 0.0)
            else:
                no_chain |= move
        if no_chain:
            no_chain._ne_infer_supply_status()

    def _ne_classify_supply_move(self, supply):
        """Walk the WHOLE chain (BFS over all branches) down to its roots and
        classify by the real driver: a PO, an MO or a receipt. An internal
        transfer is only kept as a fallback if nothing concrete is found deeper.
        """
        self.ensure_one()
        frontier = supply
        seen = set()
        fallback = None
        while frontier and len(seen) < 100:
            deeper = self.browse()
            for move in frontier:
                if move.id in seen:
                    continue
                seen.add(move.id)
                if move.purchase_line_id:
                    return move.purchase_line_id._ne_po_line_status()
                if move.production_id:
                    return move.production_id._ne_mo_status()
                pt = move.picking_id.picking_type_id.code
                if pt == "incoming":
                    return "reception", _("Reception needed")
                if pt == "internal":
                    fallback = ("to_transfer", _("Transfer needed"))
                deeper |= move.move_orig_ids.filtered(
                    lambda m: m.state not in ("done", "cancel")
                )
            frontier = deeper
        return fallback or ("reception", _("Reception needed"))

    # ------------------------------------------------------------------
    # Route inference (no chain, no stock anywhere)
    # ------------------------------------------------------------------
    def _ne_infer_supply_status(self):
        """No chain and no stock: a product with a real (non-kit) BoM must be
        manufactured, everything else must be ordered. Route refs are unreliable
        here (custom routes), so we key off the BoM."""
        for move in self:
            product = move.product_id
            if product.bom_ids.filtered(lambda b: b.type == "normal"):
                move._ne_set("to_manufacture", _("Must be manufactured"), 0.0)
            else:
                move._ne_set("to_order", _("Must be ordered"), 0.0)

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
