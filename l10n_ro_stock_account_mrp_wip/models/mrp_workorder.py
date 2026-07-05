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
            wo._l10n_ro_post_inventory()
            # Update the work in progress (Dr 331 / Cr 711) with the components
            # just consumed and the labour of this work order.
            wo.production_id._l10n_ro_update_wip()
        return res

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
