# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import models


class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    def create(self, vals_list):
        records = super().create(vals_list)
        records._l10n_ro_update_wip_from_time()
        return records

    def write(self, vals):
        res = super().write(vals)
        if "duration" in vals or "date_end" in vals:
            self._l10n_ro_update_wip_from_time()
        return res

    def _l10n_ro_update_wip_from_time(self):
        """Time logged on a *not-done* work order capitalises the labour into
        WIP (Dr 331 / Cr 711), one entry per work order."""
        workorders = self.filtered(
            lambda p: p.duration
            and p.workorder_id
            and p.workorder_id.state not in ("done", "cancel")
            and p.workorder_id.production_id.l10n_ro_auto_wip_accounting
        ).workorder_id
        if workorders:
            workorders._l10n_ro_post_labour_wip()
