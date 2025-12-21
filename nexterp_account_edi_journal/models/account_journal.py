# Copyright (C) 2025 NextERP Romania
# License LGPL-3 or later

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_ro_edi_send_enabled = fields.Boolean(
        string="Enable EDI Send",
        help="Enable sending this journal entry as an EDI document.",
        default=False,
    )
