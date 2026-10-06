# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""A payment term that falls on a fixed day of the invoice's own month.

"The 10th" means the 10th of the month the invoice is dated in, whether the
invoice was issued on the 1st or on the 28th.
"""

from datetime import date

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDayOfTheMonthTerm(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.term = cls.env["account.payment.term"].create(
            {
                "name": "Pe 10 ale lunii",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 100.0,
                            "delay_type": "day_of_the_month",
                            "nb_days": 10,
                        },
                    )
                ],
            }
        )
        cls.line = cls.term.line_ids

    def test_the_due_date_is_that_day_of_the_invoice_month(self):
        self.assertEqual(self.line._get_due_date("2026-03-22"), date(2026, 3, 10))

    def test_an_invoice_before_that_day_is_still_due_that_month(self):
        """The term says when in the month, not how long after the
        invoice."""
        self.assertEqual(self.line._get_due_date("2026-03-02"), date(2026, 3, 10))

    def test_the_first_day_of_the_month_is_day_one(self):
        self.line.nb_days = 1
        self.assertEqual(self.line._get_due_date("2026-03-22"), date(2026, 3, 1))

    def test_the_month_is_the_invoice_month_not_today(self):
        self.assertEqual(self.line._get_due_date("2026-12-31"), date(2026, 12, 10))
        self.assertEqual(self.line._get_due_date("2027-01-01"), date(2027, 1, 10))

    def test_february_is_not_a_special_case(self):
        self.assertEqual(self.line._get_due_date("2026-02-20"), date(2026, 2, 10))

    def test_the_other_delay_types_are_left_to_core(self):
        self.line.write({"delay_type": "days_after", "nb_days": 30})
        self.assertEqual(self.line._get_due_date("2026-03-22"), date(2026, 4, 21))

    def test_an_invoice_on_a_term_falls_due_on_that_day(self):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.env["res.partner"].create({"name": "Client"}).id,
                "invoice_date": "2026-03-22",
                "invoice_payment_term_id": self.term.id,
                "invoice_line_ids": [(0, 0, {"name": "Marfa", "price_unit": 100.0})],
            }
        )
        move.action_post()
        self.assertEqual(move.invoice_date_due, date(2026, 3, 10))
