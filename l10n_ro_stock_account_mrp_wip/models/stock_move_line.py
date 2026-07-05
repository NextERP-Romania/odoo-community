# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import models


class StockMoveLine(models.Model):
    _name = "stock.move.line"
    _inherit = ["stock.move.line", "l10n.ro.mixin"]

    def write(self, vals):
        res = super().write(vals)
        if "quantity" in vals and not self.env.context.get("skip_mo_check"):
            # Correcting a consumption from its move line keeps the WIP in sync.
            self.move_id._l10n_ro_sync_consumption_wip()
        return res
