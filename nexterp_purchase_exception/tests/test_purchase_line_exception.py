# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Exceptions raised by one purchase line, not by the whole order.

Core blocks the order and says so on the order; here the offending line also
carries the rule, so the buyer can see which line is the problem.
"""

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPurchaseLineException(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Furnizor"})
        cls.product = cls.env["product.product"].create(
            {"name": "Marfa", "type": "consu", "standard_price": 10.0}
        )
        cls.rule = cls.env["exception.rule"].create(
            {
                "name": "Pret zero",
                "description": "Linia nu are pret.",
                "sequence": 10,
                "model": "purchase.order.line",
                "code": "failed = not obj.price_unit",
            }
        )

    def _confirm_blocked(self, order):
        """Confirming an order with exceptions opens the popup instead of
        going through, and leaves the order where it was."""
        action = order.button_confirm()
        self.assertEqual(action["res_model"], "purchase.exception.confirm")
        self.assertEqual(order.state, "draft")

    def _order(self, price_unit):
        return self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_qty": 1,
                            "price_unit": price_unit,
                            "name": "Marfa",
                            "date_planned": "2026-03-15",
                        }
                    )
                ],
            }
        )

    def test_a_line_that_breaks_a_rule_carries_it(self):
        order = self._order(0.0)
        self._confirm_blocked(order)
        self.assertEqual(order.order_line.exception_ids, self.rule)

    def test_a_line_in_order_carries_nothing(self):
        order = self._order(10.0)
        order.button_confirm()
        self.assertFalse(order.order_line.exception_ids)

    def test_the_offending_line_is_flagged_for_the_buyer(self):
        order = self._order(0.0)
        self._confirm_blocked(order)
        self.assertTrue(order.order_line.is_exception_danger)

    def test_the_summary_names_the_rule_and_says_what_is_wrong(self):
        order = self._order(0.0)
        self._confirm_blocked(order)
        summary = order.order_line.exceptions_summary
        self.assertIn("Pret zero", summary)
        self.assertIn("Linia nu are pret.", summary)

    def test_an_exception_that_was_waved_through_stops_shouting(self):
        order = self._order(0.0)
        self._confirm_blocked(order)
        order.order_line.ignore_exception = True
        self.assertFalse(order.order_line.is_exception_danger)
        self.assertFalse(order.order_line.exceptions_summary)

    def test_only_the_offending_line_is_flagged(self):
        order = self._order(0.0)
        order.order_line = [
            Command.create(
                {
                    "product_id": self.product.id,
                    "product_qty": 1,
                    "price_unit": 10.0,
                    "name": "Marfa cu pret",
                    "date_planned": "2026-03-15",
                }
            )
        ]
        self._confirm_blocked(order)
        flagged = order.order_line.filtered("is_exception_danger")
        self.assertEqual(len(flagged), 1)
        self.assertEqual(flagged.price_unit, 0.0)

    def test_the_summary_does_not_let_html_through(self):
        """The rule text is typed by a user and ends up in a Html field."""
        self.rule.write({"name": "<b>Pret</b>", "description": "<script>x</script>"})
        order = self._order(0.0)
        self._confirm_blocked(order)
        summary = order.order_line.exceptions_summary
        self.assertNotIn("<script>", summary)
        self.assertIn("&lt;script&gt;", summary)
