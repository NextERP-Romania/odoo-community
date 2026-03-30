from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _get_default_sending_settings(self, move, from_cron=False, **custom_settings):
        res = super()._get_default_sending_settings(
            move, from_cron=from_cron, **custom_settings
        )
        if self.env.context.get("l10n_ro_send_to_anaf"):
            res["sending_methods"] = {}
        return res

    @api.model
    def _get_default_sending_methods(self, move) -> set:
        """By default, we use the sending method set on the partner or email."""
        res = super()._get_default_sending_methods(move)
        new_sending_methods = set()
        if self.env.context.get("l10n_ro_send_to_anaf"):
            for method in res:
                if method == "ro_edi":
                    new_sending_methods.add(method)
            return new_sending_methods
        else:
            return res
