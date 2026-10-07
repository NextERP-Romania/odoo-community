# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Which date a bill is booked on.

A supplier bill arrives late and is booked in the month it is dated, not in
the month it was typed in -- unless VAT for that month is already locked, in
which case it lands on the first open day.
"""

from datetime import date

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountingDateOnBills(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    def _bill(self, invoice_date, move_type="in_invoice"):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": invoice_date,
                "invoice_line_ids": [
                    (0, 0, {"product_id": self.product_a.id, "price_unit": 100.0})
                ],
            }
        )

    def test_a_bill_is_booked_on_the_day_it_is_dated(self):
        bill = self._bill("2026-03-15")
        self.assertEqual(bill.date, date(2026, 3, 15))

    def test_a_locked_month_pushes_the_bill_to_the_first_open_day(self):
        """VAT for that month is already declared; the bill cannot go back
        in."""
        self.company.tax_lock_date = "2026-03-31"
        bill = self._bill("2026-03-15")
        self.assertEqual(bill.date, date(2026, 4, 1))

    def test_a_bill_dated_on_the_lock_day_itself_is_pushed_too(self):
        self.company.tax_lock_date = "2026-03-15"
        bill = self._bill("2026-03-15")
        self.assertEqual(bill.date, date(2026, 3, 16))

    def test_a_bill_after_the_lock_stays_where_it_is(self):
        self.company.tax_lock_date = "2026-02-28"
        bill = self._bill("2026-03-15")
        self.assertEqual(bill.date, date(2026, 3, 15))

    def test_a_receipt_is_treated_like_a_bill(self):
        bill = self._bill("2026-03-15", move_type="in_receipt")
        self.assertEqual(bill.date, date(2026, 3, 15))
