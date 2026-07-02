# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

import logging

from odoo import Command, models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _name = "stock.move"
    _inherit = ["stock.move", "l10n.ro.mixin"]

    def _l10n_ro_wip_production(self):
        """Return the WIP-enabled production this move belongs to, if any.

        A move is WIP-relevant when it is a component consumption
        (``raw_material_production_id``) or the finished-goods production
        (``production_id``) of an order flagged with auto WIP accounting.
        """
        self.ensure_one()
        production = self.raw_material_production_id or self.production_id
        if production and production.l10n_ro_auto_wip_accounting:
            return production
        return production.browse()

    def _get_l10n_ro_move_type_account_list(self):
        """Reroute component and finished-goods valuation through WIP (331).

        Standard l10n_ro posts component consumption against the expense
        account and finished production against it as well. For WIP accounting
        we route both through the WIP production account so that 331
        accumulates the consumed components (and the labour posted by the work
        order) and is cleared when the finished product is produced.
        """
        res = super()._get_l10n_ro_move_type_account_list()
        if not self._l10n_ro_wip_production():
            return res
        wip_reroute = {
            "consumption": [("production_wip", "stock_valuation", "value", 1)],
            "consumption_return": [("production_wip", "stock_valuation", "value", -1)],
            "production": [("stock_valuation", "production_wip", "value", 1)],
            "production_return": [("stock_valuation", "production_wip", "value", -1)],
        }
        return wip_reroute.get(self.l10n_ro_move_type, res)

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            if not move.is_l10n_ro_record:
                continue
            production = move._l10n_ro_wip_production()
            if production and move.account_move_id:
                # Link the component / finished-goods valuation entry to the
                # manufacturing order using the native m2m, so it shows up under
                # the MO WIP entries and feeds the WIP amount computation.
                move.account_move_id.sudo().write(
                    {"wip_production_ids": [Command.link(production.id)]}
                )
        return res
