# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def unlink(self):
        for move in self:
            if not move.company_id.account_allow_delete_last_invoice:
                continue
            # `highest_name` is the last number issued BEFORE this move, so
            # when the two agree this move is the last one of its sequence and
            # its number can go back. Both are normalised to "" because the
            # first move of a sequence has `highest_name` False while
            # `_get_last_sequence()` returns None -- and `False == None` is
            # False, which used to leave that one number burned.
            last_name = move._get_last_sequence() or ""
            if (move.highest_name or "") != last_name:
                continue
            if move.name and move.name >= last_name:
                move.name = "/"
                move.posted_before = False
                move.state = "draft"
        return super().unlink()
