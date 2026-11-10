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
        # This accounting-date override only applies to Romanian companies.
        ro_country = cls.env.ref("base.ro")
        cls.company.account_fiscal_country_id = ro_country
        # A purchase tax in the RO fiscal country so the bill keeps a tax
        # (has_tax) without tripping the taxes-vs-fiscal-country validation.
        # The tax group must share the tax's country, so create both in RO.
        ro_tax_group = cls.env["account.tax.group"].create(
            {"name": "RO TVA (test)", "country_id": ro_country.id}
        )
        cls.ro_tax = cls.env["account.tax"].create(
            {
                "name": "RO TVA 19 (test)",
                "amount": 19.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "country_id": ro_country.id,
                "tax_group_id": ro_tax_group.id,
                "company_id": cls.company.id,
            }
        )

    def _bill(self, invoice_date, move_type="in_invoice"):
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": invoice_date,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_a.id,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, self.ro_tax.ids)],
                        },
                    )
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
