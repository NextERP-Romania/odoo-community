# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).

"""The register of a session, and the figures that stand next to it.

What is pinned down here is that the document printed is the Romanian
register run on the session's own statement -- not a second form -- and that
the figures the screen lists are read off that statement, including the one
gap that can be anything but zero: the drawer counted against the movements.
"""

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

REPORT = "l10n_ro_account_bank_statement_report.action_report_l10n_ro_account_statement"


@tagged("post_install", "-at_install")
class TestCashRegister(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # `cash_control` is computed off the payment methods, so a till
        # without a cash one never opens a statement and has no register.
        # A cash payment method cannot be shared between two tills, so the
        # test brings its own drawer rather than borrowing another shop's.
        journal = cls.env["account.journal"].create(
            {
                "name": "Register Test Cash",
                "type": "cash",
                "code": "RTC",
                "company_id": cls.env.company.id,
            }
        )
        cls.cash_method = cls.env["pos.payment.method"].create(
            {"name": "Register Cash", "type": "cash", "journal_id": journal.id}
        )
        cls.config = cls.env["pos.config"].create(
            {
                "name": "Register Shop",
                "payment_method_ids": [(6, 0, cls.cash_method.ids)],
            }
        )
        assert cls.config.cash_control, "the test till must keep cash"

    def _open(self, opening=0.0):
        self.config.open_ui()
        session = self.config.current_session_id
        session.set_opening_control(opening, "")
        return session

    def test_the_register_is_the_romanian_one_on_the_session_statement(self):
        """No second form: the existing report, on `bank_statement_id`."""
        session = self._open(100)
        action = session.action_l10n_ro_print_cash_register()
        if action.get("type") == "ir.actions.act_window":
            # `report_action` wraps itself in the document layout wizard
            # while the company has not configured one; the report it will
            # run afterwards is carried in the context.
            action = action["context"]["report_action"]
        self.assertEqual(action["report_name"], self.env.ref(REPORT).report_name)
        self.assertEqual(action["context"]["active_ids"], session.bank_statement_id.ids)

    def test_a_session_without_cash_has_no_register(self):
        """Saying so is more use than an empty form."""
        cashless = self.env["pos.config"].create(
            {"name": "Cashless Shop", "payment_method_ids": [(6, 0, [])]}
        )
        self.assertFalse(cashless.cash_control)
        session = self.env["pos.session"].create({"config_id": cashless.id})
        self.assertFalse(session.bank_statement_id)
        with self.assertRaises(UserError):
            session.action_l10n_ro_print_cash_register()
        row = next(
            row
            for row in cashless.pos_cash_register_sessions()
            if row["id"] == session.id
        )
        self.assertFalse(row["statement_id"])

    def test_the_listed_figures_are_read_off_the_statement(self):
        """And they mean what the statement means, not what they look like.

        The opening is NOT what the cashier counted into the drawer: core
        carries it over from the close of the previous session
        (`_get_opening_balance`) and writes what was counted as a line, so
        a till opening for the first time starts at nothing and the money
        put in is a movement. The register has to read that way round, or
        the first day of a shop would show an opening nobody booked.
        """
        session = self._open(100)
        statement = session.bank_statement_id
        row = next(
            row
            for row in self.config.pos_cash_register_sessions()
            if row["id"] == session.id
        )
        self.assertEqual(row["statement_id"], statement.id)
        self.assertEqual(row["opening"], statement.balance_start)
        self.assertEqual(row["expected"], statement.balance_end)
        self.assertEqual(row["movements"], row["expected"] - row["opening"])

        self.assertEqual(row["opening"], 0, "a new till opens on nothing")
        self.assertEqual(row["movements"], 100, "what was counted in is a movement")

    def test_the_gap_shown_is_the_drawer_against_the_movements(self):
        """Counted less expected -- the only figure that can surprise.

        The session's own `opening_balance` and `closing_balance` are
        related fields onto this statement, so comparing those two would be
        comparing a value with itself.
        """
        session = self._open(100)
        statement = session.bank_statement_id
        self.assertEqual(session.opening_balance, statement.balance_start)
        self.assertEqual(session.closing_balance, statement.balance_end_real)

        statement.balance_end_real = statement.balance_end + 25
        row = next(
            row
            for row in self.config.pos_cash_register_sessions()
            if row["id"] == session.id
        )
        self.assertEqual(row["counted"], statement.balance_end + 25)
        self.assertEqual(row["difference"], 25)
        self.assertFalse(row["balanced"])

    def test_a_balanced_drawer_is_said_to_be_balanced(self):
        session = self._open(100)
        statement = session.bank_statement_id
        statement.balance_end_real = statement.balance_end
        row = next(
            row
            for row in self.config.pos_cash_register_sessions()
            if row["id"] == session.id
        )
        self.assertEqual(row["difference"], 0)
        self.assertTrue(row["balanced"])
