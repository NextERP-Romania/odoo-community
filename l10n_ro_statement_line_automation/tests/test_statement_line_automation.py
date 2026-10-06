# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""One bank statement per journal per day, built as the lines arrive.

Romanian practice is one statement per banking day. Lines imported one by one
would otherwise sit outside any statement, so each line joins the statement of
its own day -- creating it the first time.
"""

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestStatementLineAutomation(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.company_data["default_journal_bank"]
        cls.other_journal = cls.journal.copy({"name": "Banca 2", "code": "BNK2"})

    def _line(self, amount=100.0, date="2026-03-15", journal=None, **vals):
        return self.env["account.bank.statement.line"].create(
            {
                "journal_id": (journal or self.journal).id,
                "date": date,
                "payment_ref": "Incasare",
                "amount": amount,
                **vals,
            }
        )

    def test_a_line_on_its_own_opens_the_statement_of_its_day(self):
        line = self._line()
        self.assertTrue(line.statement_id)
        self.assertEqual(line.statement_id.journal_id, self.journal)
        self.assertEqual(str(line.statement_id.date), "2026-03-15")

    def test_a_second_line_of_the_same_day_joins_the_same_statement(self):
        first = self._line()
        second = self._line(amount=50.0)
        self.assertEqual(second.statement_id, first.statement_id)

    def test_another_day_gets_a_statement_of_its_own(self):
        first = self._line(date="2026-03-15")
        second = self._line(date="2026-03-16")
        self.assertNotEqual(second.statement_id, first.statement_id)

    def test_another_bank_gets_a_statement_of_its_own(self):
        first = self._line()
        second = self._line(journal=self.other_journal)
        self.assertNotEqual(second.statement_id, first.statement_id)

    def test_a_line_that_already_names_its_statement_is_left_alone(self):
        statement = self.env["account.bank.statement"].create(
            {
                "journal_id": self.journal.id,
                "date": "2026-03-10",
                "name": "Extras pus de mana",
            }
        )
        line = self._line(statement_id=statement.id)
        self.assertEqual(line.statement_id, statement)

    def test_the_closing_balance_counts_the_lines_that_joined(self):
        line = self._line(amount=100.0)
        self._line(amount=50.0)
        self.assertEqual(line.statement_id.balance_end, 150.0)

    def test_a_company_outside_romania_is_not_touched(self):
        """This is a Romanian practice, not Odoo's way of working."""
        foreign = self.setup_other_company(name="Firma DE")["company"]
        foreign.country_id = self.env.ref("base.de")
        journal = (
            self.env["account.journal"]
            .with_company(foreign)
            .create({"name": "Banca DE", "code": "BDE", "type": "bank"})
        )
        line = (
            self.env["account.bank.statement.line"]
            .with_company(foreign)
            .create(
                {
                    "journal_id": journal.id,
                    "date": "2026-03-15",
                    "payment_ref": "Incasare",
                    "amount": 100.0,
                }
            )
        )
        self.assertFalse(line.statement_id)
