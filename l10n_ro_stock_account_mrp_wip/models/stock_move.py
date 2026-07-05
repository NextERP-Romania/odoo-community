# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import models


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move", "l10n.ro.mixin"]

    def _l10n_ro_wip_production(self):
        """Return the WIP-enabled production this move belongs to, if any.

        A move is WIP-relevant when it is a component consumption
        (``raw_material_production_id``) or the finished-goods production
        (``production_id``) of an order flagged with auto WIP accounting.

        The stock valuation notes themselves are left to the standard l10n_ro
        flow (component consumption ``601 = 301``, finished production
        ``345 = 711``); the WIP note (``331 = 711``) is produced by the
        standard Odoo WIP wizard, run automatically on consumption, work order
        finish and time logged on a not-done work order.
        """
        self.ensure_one()
        production = self.raw_material_production_id or self.production_id
        if production and production.l10n_ro_auto_wip_accounting:
            return production
        return production.browse()

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        # Each component consumption posts its own WIP entry (Dr 331 / Cr 711)
        # with the consumed product on the lines. Finished-goods moves are
        # handled when the order is marked done (WIP is cleared there).
        for move in self:
            production = move._l10n_ro_wip_production()
            if not production or not move.raw_material_production_id:
                continue
            production._l10n_ro_post_wip_entry(
                move._get_l10n_ro_value("value"),
                product=move.product_id,
                label=move.env._(
                    "WIP consumption - %(product)s",
                    product=move.product_id.display_name,
                ),
            )
        return res
