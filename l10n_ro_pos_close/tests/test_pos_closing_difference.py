# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).
"""What the cashier counted, kept long enough to be explained.

Core settles the difference of a payment method into the profit or loss
account of its journal and keeps neither the amount it expected nor the amount
it was given. These tests pin down that both survive the closing, and that the
case the report exists for -- takings cashed in on the card while the money
went into the drawer -- comes out of it as a surplus covering a shortage.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import CommonPosTest


@tagged("post_install", "-at_install")
class TestPosClosingDifference(CommonPosTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.pos_config_usd
        cls.cash = cls.cash_payment_method
        cls.bank = cls.bank_payment_method

    def _open_session(self, opening_cash=0):
        self.config.open_ui()
        session = self.config.current_session_id
        session.set_opening_control(opening_cash, "")
        return session

    def _order(self, session, payments):
        """One order of 100, paid as asked."""
        order, _refund = self.create_backend_pos_order(
            {
                "pos_config": self.config,
                "line_data": [
                    {
                        "product_id": self.ten_dollars_no_tax.product_variant_id.id,
                        "qty": 10,
                    },
                ],
                "payment_data": [
                    {"payment_method_id": method.id, "amount": amount}
                    for method, amount in payments
                ],
            }
        )
        self.assertEqual(order.session_id, session)
        return order

    def _line(self, session, method):
        return session.l10n_ro_closing_line_ids.filtered(
            lambda line, method=method: line.payment_method_id == method
        )

    # -- the snapshot ------------------------------------------------------

    def test_what_the_cashier_counted_survives_the_closing(self):
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.close_session_from_ui({str(self.bank.id): 90, str(self.cash.id): 0})

        line = self._line(session, self.bank)
        self.assertEqual(line.expected_amount, 100)
        self.assertEqual(line.counted_amount, 90)
        self.assertEqual(line.difference, -10)
        self.assertTrue(line.has_difference)
        self.assertTrue(session.l10n_ro_has_closing_difference)
        self.assertEqual(session.l10n_ro_closing_shortage, 10)
        self.assertEqual(session.l10n_ro_closing_difference, -10)

    def test_the_cash_counted_is_measured_against_the_drawer(self):
        # The drawer holds the opening float and the cash takings, which is
        # the balance core itself compares the count against.
        session = self._open_session(opening_cash=50)
        self._order(session, [(self.cash, 100)])
        session.close_session_from_ui({str(self.cash.id): 150, str(self.bank.id): 0})

        line = self._line(session, self.cash)
        self.assertEqual(line.expected_amount, 150)
        self.assertEqual(line.counted_amount, 150)
        self.assertFalse(line.has_difference)
        self.assertFalse(session.l10n_ro_has_closing_difference)

    def test_a_method_the_register_did_not_count_is_left_out(self):
        # Core skips the reconciliation of such a method, so there is nothing
        # to hold the cashier to either.
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.close_session_from_ui({str(self.cash.id): 0})

        self.assertFalse(self._line(session, self.bank))
        self.assertTrue(self._line(session, self.cash))

    def test_a_method_that_is_neither_cash_nor_bank_is_not_controlled(self):
        session = self._open_session()
        session.close_session_from_ui({str(self.cash.id): 0, str(self.bank.id): 0})
        self.assertFalse(self._line(session, self.credit_payment_method))

    def test_closing_twice_does_not_double_the_control(self):
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.close_session_from_ui({str(self.bank.id): 100, str(self.cash.id): 0})
        count = len(session.l10n_ro_closing_line_ids)
        session.close_session_from_ui({str(self.bank.id): 100, str(self.cash.id): 0})
        self.assertEqual(len(session.l10n_ro_closing_line_ids), count)

    # -- takings on the wrong payment method -------------------------------

    def test_takings_on_the_wrong_method_cover_each_other(self):
        # The order was cashed in on the card, the money went into the drawer:
        # the till is right, the split between the methods is not.
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.close_session_from_ui({str(self.bank.id): 0, str(self.cash.id): 100})

        self.assertEqual(self._line(session, self.bank).difference, -100)
        self.assertEqual(self._line(session, self.cash).difference, 100)
        self.assertEqual(session.l10n_ro_closing_surplus, 100)
        self.assertEqual(session.l10n_ro_closing_shortage, 100)
        self.assertEqual(session.l10n_ro_closing_difference, 0)
        self.assertTrue(session.l10n_ro_has_closing_difference)
        self.assertTrue(session._l10n_ro_is_balanced())

    def test_a_session_that_adds_up_is_not_called_balanced(self):
        # Nothing to cover, nothing to explain.
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.close_session_from_ui({str(self.bank.id): 100, str(self.cash.id): 0})
        self.assertFalse(session._l10n_ro_is_balanced())

    # -- the explanation typed in the register -----------------------------

    def test_what_the_cashier_typed_in_the_register_reaches_the_line(self):
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.l10n_ro_set_closing_explanations(
            {
                str(self.bank.id): {
                    "reason": "wrong_method",
                    "note": "Cashed in on the card, taken in cash.",
                }
            },
            "Nothing else to report.",
        )
        session.close_session_from_ui({str(self.bank.id): 0, str(self.cash.id): 100})

        line = self._line(session, self.bank)
        self.assertEqual(line.reason, "wrong_method")
        self.assertEqual(line.note, "Cashed in on the card, taken in cash.")
        # Core collects the closing note in the same popup and drops it.
        self.assertEqual(session.closing_notes, "Nothing else to report.")
        self.assertEqual(session.l10n_ro_closing_notes, "Nothing else to report.")

    def test_a_cause_that_is_not_ours_is_refused(self):
        # The cause comes from the browser; the explanation is free text.
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.l10n_ro_set_closing_explanations(
            {str(self.bank.id): {"reason": "stolen", "note": "Kept anyway."}}
        )
        session.close_session_from_ui({str(self.bank.id): 90, str(self.cash.id): 0})

        line = self._line(session, self.bank)
        self.assertFalse(line.reason)
        self.assertEqual(line.note, "Kept anyway.")

    def test_a_closing_nobody_explained_leaves_the_lines_blank(self):
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.close_session_from_ui({str(self.bank.id): 90, str(self.cash.id): 0})

        line = self._line(session, self.bank)
        self.assertFalse(line.reason)
        self.assertFalse(line.note)

    # -- the explanation and the report ------------------------------------

    def test_the_note_reaches_the_lines_and_the_session(self):
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.close_session_from_ui({str(self.bank.id): 0, str(self.cash.id): 100})

        wizard = (
            self.env["l10n.ro.pos.closing.note"]
            .with_context(default_session_id=session.id)
            .create({})
        )
        self.assertEqual(len(wizard.line_ids), len(session.l10n_ro_closing_line_ids))
        wizard.note = "Cashed in on the card, taken in cash."
        wizard.line_ids.filtered(
            lambda line: line.payment_method_id == self.bank
        ).reason = "wrong_method"
        wizard.action_save()

        self.assertEqual(
            session.l10n_ro_closing_notes, "Cashed in on the card, taken in cash."
        )
        self.assertEqual(self._line(session, self.bank).reason, "wrong_method")

    def test_the_differences_first_in_the_report(self):
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.close_session_from_ui({str(self.bank.id): 90, str(self.cash.id): 0})
        self.assertEqual(
            session._l10n_ro_report_lines()[0], self._line(session, self.bank)
        )

    def test_the_report_renders(self):
        # The document is printed in the language of the company, which on a
        # Romanian database is Romanian: assert on what does not get
        # translated, the session and the payment method.
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.close_session_from_ui({str(self.bank.id): 90, str(self.cash.id): 0})
        html = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_ro_pos_close.report_pos_session_closing", session.ids
        )[0]
        self.assertIn(session.name.encode(), html)
        self.assertIn(self.bank.name.encode(), html)

    def test_the_report_is_printed_in_the_language_of_the_company(self):
        session = self._open_session()
        self._order(session, [(self.bank, 100)])
        session.close_session_from_ui({str(self.bank.id): 90, str(self.cash.id): 0})
        self.env.company.partner_id.lang = "en_US"
        html = self.env["ir.actions.report"]._render_qweb_html(
            "l10n_ro_pos_close.report_pos_session_closing", session.ids
        )[0]
        self.assertIn(b"Report of Differences", html)

    def test_a_session_closed_before_the_module_has_nothing_to_report(self):
        session = self._open_session()
        session.close_session_from_ui({str(self.cash.id): 0, str(self.bank.id): 0})
        session.l10n_ro_closing_line_ids.unlink()
        with self.assertRaises(UserError):
            session.action_l10n_ro_print_closing_report()
