# Copyright (C) 2025 NextERP Romania
# License LGPL-3 or later

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_ro_edi_send_enabled = models.Boolean(
        string="Enable EDI Send",
        help="Enable sending this journal entry as an EDI document.",
        default=False,
    )
