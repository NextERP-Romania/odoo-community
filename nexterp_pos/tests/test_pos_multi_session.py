# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Several days open on one register, closed oldest first.

The cash of a register is a chain: each session opens where the one before it
ended. Core keeps that chain honest by allowing one session at a time; this
module allows several, so it has to rebuild the chain itself as they close.
"""

from datetime import datetime

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import CommonPosTest


@tagged("post_install", "-at_install")
class TestPosMultiSession(CommonPosTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.pos_config_usd
        cls.config.pos_multi_session = True

    def _session(self, day, state="opened"):
        session = self.env["pos.session"].create({"config_id": self.config.id})
        session.start_at = datetime(2026, 3, day, 9, 0, 0)
        session.state = state
        return session

    # -- which session the register is on --------------------------------

    def test_the_current_session_is_the_oldest_open_one(self):
        # Core would answer with the newest; the till is still on the oldest.
        oldest = self._session(1)
        self._session(2)
        self.config.invalidate_recordset()
        self.assertEqual(self.config.current_session_id, oldest)

    def test_a_named_session_wins_over_the_oldest(self):
        self._session(1)
        asked_for = self._session(2)
        config = self.config.with_context(session_id=asked_for.id)
        config.invalidate_recordset()
        self.assertEqual(config.current_session_id, asked_for)

    def test_a_register_without_the_setting_keeps_core_behaviour(self):
        # Core allows one open session at a time, and that rule is what keeps
        # a cashier from opening a second till by accident. Lifting it for
        # every register would be the real regression here.
        self.config.pos_multi_session = False
        self._session(1)
        with self.assertRaises(ValidationError):
            self._session(2)

    def test_sessions_not_yet_started_fall_back_to_creation_order(self):
        # ``start_at`` is stamped by the cash control, not by create, so a
        # register can hold sessions that have no opening time yet.
        first = self.env["pos.session"].create({"config_id": self.config.id})
        self.env["pos.session"].create({"config_id": self.config.id})
        self.config.invalidate_recordset()
        self.assertFalse(first.start_at)
        self.assertEqual(self.config.current_session_id, first)

    def test_the_statistics_follow_the_oldest_open_session(self):
        oldest = self._session(1)
        newest = self._session(2)
        self.assertIsInstance(self.config.get_statistics_for_session(newest), dict)
        self.assertEqual(self.config._pos_multi_session_oldest_open(), oldest)

    # -- the order they close in -----------------------------------------

    def test_opening_is_refused_while_an_older_session_is_open(self):
        self._session(1)
        self._session(2)
        with self.assertRaises(ValidationError):
            self.config.with_context(
                session_id=self._session(3).id
            )._action_to_open_ui()

    def test_opening_is_allowed_once_the_older_ones_are_closed(self):
        self._session(1, state="closed")
        current = self._session(2)
        action = self.config.with_context(session_id=current.id)._action_to_open_ui()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertIn(f"session_id={current.id}", action["url"])

    # -- the cash chain ---------------------------------------------------

    def test_closing_hands_the_drawer_to_the_session_behind(self):
        first = self._session(1)
        second = self._session(2)
        third = self._session(3)
        first.cash_register_balance_end_real = 500.0
        first._validate_session()
        second.invalidate_recordset()
        third.invalidate_recordset()
        # The second starts where the first ended; the third still has an open
        # session in front of it, so it has nothing real to start from yet.
        self.assertEqual(second.cash_register_balance_start, 500.0)
        self.assertEqual(third.cash_register_balance_start, 0.0)

    def test_a_register_without_the_setting_rebuilds_nothing(self):
        first = self._session(1)
        second = self._session(2)
        # Both exist; now the register goes back to one session at a time.
        self.config.pos_multi_session = False
        second.cash_register_balance_start = 42.0
        first.cash_register_balance_end_real = 500.0
        first._validate_session()
        second.invalidate_recordset()
        self.assertEqual(second.cash_register_balance_start, 42.0)

    # -- the opening time -------------------------------------------------

    def test_the_opening_time_survives_the_cash_control(self):
        session = self._session(1)
        opened_at = session.start_at
        session.set_opening_control(0, "")
        self.assertEqual(session.start_at, opened_at)
