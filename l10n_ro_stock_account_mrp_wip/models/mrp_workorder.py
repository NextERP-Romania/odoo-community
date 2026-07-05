# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import models
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _name = "mrp.workorder"
    _inherit = ["mrp.workorder", "l10n.ro.mixin"]

    def button_finish(self):
        ro_not_finished = self.filtered(
            lambda wo: wo.is_l10n_ro_record and wo.state != "done"
        )
        res = super().button_finish()
        for wo in ro_not_finished:
            if not wo.production_id.l10n_ro_auto_wip_accounting:
                continue
            # Post the raw material consumption at the end of the work order so
            # stock and accounting entries happen together (Dr 601 / Cr 301).
            # Each consumption move posts its own WIP entry (Dr 331 / Cr 711).
            wo._l10n_ro_post_inventory()
            # Capitalise the labour of this work order into WIP.
            wo._l10n_ro_post_labour_wip()
        return res

    def _l10n_ro_post_labour_wip(self):
        """Post the labour WIP entry (Dr 331 / Cr 711) for each work order, for
        the labour recorded so far that is not yet capitalised (incremental per
        work order). The finished product is kept on the lines."""
        for wo in self:
            production = wo.production_id
            if not production.l10n_ro_auto_wip_accounting or wo.state == "cancel":
                continue
            wip_account = production._get_l10n_ro_wip_account()
            if not wip_account:
                continue
            posted_moves = (
                self.env["account.move"]
                .sudo()
                .search(
                    [
                        ("l10n_ro_wip_workorder_id", "=", wo.id),
                        ("state", "=", "posted"),
                    ]
                )
            )
            already = sum(
                posted_moves.line_ids.filtered(
                    lambda line, acc=wip_account: line.account_id == acc
                ).mapped("balance")
            )
            delta = wo._cal_cost() - already
            production._l10n_ro_post_wip_entry(
                delta,
                product=production.product_id,
                label=production.env._("WIP labour - %(wo)s", wo=wo.display_name),
                workorder=wo,
            )

    def _l10n_ro_post_inventory(self):
        moves_not_available = self.move_raw_ids.filtered(
            lambda m: m.state not in ("assigned", "done", "cancel")
        )
        if moves_not_available:
            raise UserError(
                self.env._(
                    "Cannot finish the work order as some raw material moves are "
                    "not available.\nPlease check the availability of the "
                    "following moves:\n%(moves)s",
                    moves="\n".join(
                        f"- {move.raw_material_production_id.name} - "
                        f"{move.workorder_id.name} (Product: "
                        f"{move.product_id.display_name}, Qty: "
                        f"{move.product_uom_qty} {move.product_uom.name})"
                        for move in moves_not_available
                    ),
                )
            )
        moves_to_do = self.env["stock.move"]
        for move in self.move_raw_ids:
            if move.state == "assigned":
                move.picked = True
                moves_to_do |= move

        moves_to_do.with_context(skip_mo_check=True)._action_done()
        return True
