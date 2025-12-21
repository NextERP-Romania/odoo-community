# Copyright (C) 2025 NextERP Romania
# License LGPL-3 or later

from odoo import models


class AccountEdiXmlCIUSRO(models.Model):
    _inherit = "account.edi.format"

    def _is_required_for_invoice(self, invoice):
        if self.code == "cius_ro" and not invoice.journal_id.l10n_ro_edi_send_enabled:
            return False
        return super()._is_required_for_invoice(invoice)
