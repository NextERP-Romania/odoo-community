# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import api, models


class PosSession(models.Model):
    _inherit = "pos.session"

    @api.constrains("config_id")
    def _check_pos_config(self):
        """Let a register hold more than one open session.

        Core allows exactly one, which is what makes the rest of this module
        unreachable without it: the second session never gets created. The
        rule stays for every register that has not asked for the opposite --
        it is what keeps a cashier from opening a second till by accident.
        """
        others = self.filtered(lambda s: not s.config_id.pos_multi_session)
        return super(PosSession, others)._check_pos_config()

    def _validate_session(
        self,
        balancing_account=False,
        amount_to_balance=0,
        bank_payment_method_diffs=None,
    ):
        """Hand the closed drawer on to the sessions still open behind it.

        Core sets a session's opening balance from the previous session when
        it starts, which is right as long as they run one at a time. With
        several open at once the sessions behind this one were opened while
        this drawer was still counting, so their opening balance is stale the
        moment it closes. Rebuild it here, oldest first, each from the real
        end balance of whatever session precedes it -- which is zero while an
        earlier one is still open, and becomes real as the chain closes down.
        """
        res = super()._validate_session(
            balancing_account=balancing_account,
            amount_to_balance=amount_to_balance,
            bank_payment_method_diffs=bank_payment_method_diffs,
        )
        if not self.config_id.pos_multi_session:
            return res
        later_sessions = self.search(
            [
                ("config_id", "=", self.config_id.id),
                ("state", "!=", "closed"),
                ("start_at", ">", self.start_at),
            ],
            order="start_at asc",
        )
        for session in later_sessions:
            previous_session = self.search(
                [
                    ("config_id", "=", session.config_id.id),
                    ("start_at", "<", session.start_at),
                ],
                order="start_at desc",
                limit=1,
            )
            session.cash_register_balance_start = (
                previous_session.cash_register_balance_end_real
            )
        return res

    def open_frontend_cb(self):
        """Open THIS session, not whichever core considers current.

        Core reopens the last session created. With several open the cashier
        picked one from the list, and that is the one to land in.
        """
        if self and self.config_id.pos_multi_session:
            self = self.with_context(session_id=self.id)
        return super().open_frontend_cb()

    def set_opening_control(self, cashbox_value: int, notes: str):
        """Keep the opening time the session already had.

        A session opened days ago -- or synced from an external back-end with
        its own timestamp -- is stamped again by core when the cash control is
        filled in. That would reorder the register's open sessions, which are
        closed by ``start_at``.
        """
        start_at = self.start_at
        res = super().set_opening_control(cashbox_value, notes)
        if start_at:
            self.start_at = start_at
        return res
