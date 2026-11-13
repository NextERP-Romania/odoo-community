# Copyright 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_analytic_distribution_arguments(self, root_plans):
        # Punctul de extensie prevazut de core exact pentru asta ("This
        # function aims to be overridden by partner submodules").
        # Fara jurnal in argumente, `_get_applicable_models` ar cauta mereu
        # `journal_id in [False, False]` si modelele fixate pe un jurnal nu
        # s-ar aplica niciodata.
        return {
            **super()._get_analytic_distribution_arguments(root_plans),
            "journal_id": self.journal_id.id,
        }
