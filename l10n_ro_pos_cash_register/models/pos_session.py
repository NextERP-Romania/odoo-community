# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).

from odoo import models
from odoo.exceptions import UserError

REPORT = "l10n_ro_account_bank_statement_report.action_report_l10n_ro_account_statement"


class PosSession(models.Model):
    """The cash register of a session.

    A shop keeping its takings in a drawer owes a *registru de casă* for
    every day the drawer was open, and a session is exactly that: it opens
    on a counted balance, every movement is written against it, and it
    closes on another count.

    Nothing of that has to be assembled here. A session with cash control
    carries an `account.bank.statement` of its own -- `bank_statement_id`,
    core's own field -- and the Romanian register form is already written
    for that model. So this prints the existing report on the existing
    record: one form for the till and for the bank, and no second
    implementation to drift away from the first.
    """

    _inherit = "pos.session"

    def _l10n_ro_cash_register_statement(self):
        """The statement the register is drawn from, refusing to guess.

        A session without cash control never opened a drawer, so it has no
        register to print -- saying that is more use than an empty form.
        """
        self.ensure_one()
        statement = self.bank_statement_id
        if not statement:
            raise UserError(
                self.env._(
                    "%(session)s kept no cash: it has no register to print. "
                    "Only the sessions of a point of sale with cash control "
                    "have one.",
                    session=self.display_name,
                )
            )
        return statement

    def action_l10n_ro_print_cash_register(self):
        self.ensure_one()
        statement = self._l10n_ro_cash_register_statement()
        return self.env.ref(REPORT).report_action(statement)
