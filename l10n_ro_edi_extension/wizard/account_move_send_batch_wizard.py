from odoo import models


class AccountMoveSendBatchWizard(models.TransientModel):
    _inherit = "account.move.send.batch.wizard"

    def _compute_summary_data(self):
        # EXTENDS 'account'
        res = super()._compute_summary_data()
        if self.env.context.get("l10n_ro_send_to_anaf"):
            for wizard in self:
                for key, value in wizard.summary_data.items():
                    if key != "ro_edi":
                        wizard.summary_data[key] = {}
        return res
