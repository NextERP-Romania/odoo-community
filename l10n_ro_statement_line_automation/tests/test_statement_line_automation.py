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

    # ------------------------------------------------------------------
    # Extrase introduse de utilizator
    # ------------------------------------------------------------------
    def _user_statement(self, amount, balance_end_real, date="2026-03-15"):
        return self.env["account.bank.statement"].create(
            {
                "journal_id": self.journal.id,
                "date": date,
                "name": "Extras banca",
                "balance_end_real": balance_end_real,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "journal_id": self.journal.id,
                            "date": date,
                            "payment_ref": "Linie extras",
                            "amount": amount,
                        },
                    )
                ],
            }
        )

    def test_a_complete_statement_of_the_user_is_not_extended(self):
        statement = self._user_statement(100.0, 100.0)
        self.assertTrue(statement.is_complete)
        line = self._line(amount=40.0)
        self.assertNotEqual(line.statement_id, statement)
        self.assertTrue(line.statement_id.l10n_ro_auto_statement)
        self.assertEqual(statement.balance_end_real, 100.0)
        self.assertEqual(len(statement.line_ids), 1)

    def test_an_incomplete_statement_of_the_user_keeps_its_ending_balance(self):
        statement = self._user_statement(100.0, 300.0)
        self.assertFalse(statement.is_complete)
        line = self._line(amount=40.0)
        self.assertEqual(line.statement_id, statement)
        self.assertEqual(statement.balance_end, 140.0)
        self.assertEqual(statement.balance_end_real, 300.0)

    def test_the_daily_statement_ending_balance_follows_its_lines(self):
        line = self._line(amount=100.0)
        statement = line.statement_id
        self.assertTrue(statement.l10n_ro_auto_statement)
        self._line(amount=50.0)
        self.assertEqual(statement.balance_end_real, 150.0)
        self.assertTrue(statement.is_complete)

    def test_lines_of_two_companies_created_together(self):
        foreign = self.setup_other_company(name="Firma DE")["company"]
        foreign.country_id = self.env.ref("base.de")
        journal_de = (
            self.env["account.journal"]
            .with_company(foreign)
            .create({"name": "Banca DE", "code": "BDE", "type": "bank"})
        )
        lines = (
            self.env["account.bank.statement.line"]
            .with_context(allowed_company_ids=[self.journal.company_id.id, foreign.id])
            .create(
                [
                    {
                        "journal_id": self.journal.id,
                        "date": "2026-03-15",
                        "payment_ref": "RO",
                        "amount": 10.0,
                    },
                    {
                        "journal_id": journal_de.id,
                        "date": "2026-03-15",
                        "payment_ref": "DE",
                        "amount": 20.0,
                    },
                ]
            )
        )
        self.assertTrue(lines[0].statement_id)
        self.assertEqual(lines[0].statement_id.company_id, self.journal.company_id)
        self.assertFalse(lines[1].statement_id)

    # ------------------------------------------------------------------
    # Flux complet
    # ------------------------------------------------------------------
    def test_flow_a_banking_day_from_import_to_reconciled_statement(self):
        """Two lines of the day land in one statement, posted, with the
        right balances; a line of the next day opens the next statement,
        starting from the closing balance of the first."""
        first = self._line(amount=100.0)
        second = self._line(amount=-30.0)
        day = first.statement_id
        self.assertEqual(second.statement_id, day)
        self.assertEqual(day.line_ids, first | second)
        self.assertEqual(set(day.line_ids.mapped("state")), {"posted"})
        self.assertRecordValues(
            day, [{"balance_end": 70.0, "balance_end_real": 70.0, "is_complete": True}]
        )
        self.assertEqual(first.move_id.state, "posted")
        self.assertEqual(sum(first.move_id.line_ids.mapped("debit")), 100.0)
        next_line = self._line(amount=10.0, date="2026-03-16")
        next_day = next_line.statement_id
        self.assertNotEqual(next_day, day)
        self.assertEqual(next_day.balance_start, 70.0)
        self.assertEqual(next_day.balance_end_real, 80.0)
