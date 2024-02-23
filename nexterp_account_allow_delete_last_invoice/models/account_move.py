# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def unlink(self):
        for move in self:
            highest_name = move._get_last_sequence(lock=False)
            if (
                move.highest_name == highest_name
                and move.company_id.account_allow_delete_last_invoice
            ):
                if move.name >= highest_name:
                    move.name = "/"
                    move.posted_before = False
                    move.state = "draft"
        return super(AccountMove, self).unlink()
