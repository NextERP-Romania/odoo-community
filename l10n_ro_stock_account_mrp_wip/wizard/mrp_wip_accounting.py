# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from datetime import datetime

from odoo import Command, models


class MrpAccountWipAccounting(models.TransientModel):
    _inherit = "mrp.account.wip.accounting"

    def _get_line_vals(self, productions=False, date=False):
        """Romanian WIP note: ``331 = 711``.

        Components are expensed at consumption time through the regular stock
        move (Dr 601 / Cr 301). At period end this wizard only recognises the
        cost of the work in progress as an asset, debiting the WIP production
        account (331) against its counterpart (711 - venituri aferente
        costurilor stocurilor de produse). The note is reversed on the next
        period so the finished-goods entry can take over.
        """
        company = self.env.company
        if not company.l10n_ro_accounting:
            return super()._get_line_vals(productions=productions, date=date)

        if not productions:
            productions = self.env["mrp.production"]
        if not date:
            date = datetime.now().replace(hour=23, minute=59, second=59)

        compo_value = sum(
            ml.quantity_product_uom
            * (
                ml.product_id.lot_valuated
                and ml.lot_id
                and ml.lot_id.standard_price
                or ml.product_id.standard_price
            )
            for ml in productions.move_raw_ids.move_line_ids.filtered(
                lambda ml: ml.picked and ml.quantity and ml.date <= date
            )
        )
        overhead_value = productions.workorder_ids._cal_cost(date)
        # 711 counterpart (WIP overhead / production income account).
        counterpart = self._get_overhead_account()
        # 331 WIP production account.
        wip_account = company.account_production_wip_account_id.id

        return [
            Command.create(
                {
                    "label": self.env._("WIP - Component Value"),
                    "credit": compo_value,
                    "account_id": counterpart,
                }
            ),
            Command.create(
                {
                    "label": self.env._("WIP - Overhead"),
                    "credit": overhead_value,
                    "account_id": counterpart,
                }
            ),
            Command.create(
                {
                    "label": self.env._(
                        "Manufacturing WIP - %(orders_list)s",
                        orders_list=productions.mapped("name")
                        or self.env._("Manual Entry"),
                    ),
                    "debit": compo_value + overhead_value,
                    "account_id": wip_account,
                }
            ),
        ]
