# Copyright (C) 2025 NextERP Romania
# License LGPL-3 or later

from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _is_ro_edi_applicable(self, move):
        if not move.journal_id.l10n_ro_edi_send_enabled:
            return False
        return super()._is_ro_edi_applicable(move)
