# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    debt_recovery = fields.Boolean()
    debt_recovery_done = fields.Boolean()
    debt_recovery_text = fields.Text()
    payment_state = fields.Selection(
        selection_add=[("debt_recovery", "Debt Recovery")],
        ondelete={"debt_recovery": "cascade"},
    )

    def action_mark_as_debt_recovery(self):
        self.ensure_one()
        if self.company_id.account_allow_debt_recovery_invoice:
            self.debt_recovery = True
            self.payment_state = "debt_recovery"
            receivable_line = self.line_ids.filtered(
                lambda line: line.account_id.account_type == "asset_receivable"
            )
            receivable_line.blocked = True

    def _compute_amount(self):
        res = super()._compute_amount()
        for move in self:
            if move.debt_recovery:
                if move.payment_state == "paid":
                    move.debt_recovery_done = True
                    receivable_line = move.line_ids.filtered(
                        lambda line: line.account_id.account_type == "asset_receivable"
                    )
                    receivable_line.blocked = False
                else:
                    move.payment_state = "debt_recovery"
        return res
