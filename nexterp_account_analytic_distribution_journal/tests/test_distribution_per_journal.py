# Copyright 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Analytic distribution models pinned to one journal.

The same partner can be booked in several journals; a model pinned to one of
them must apply there and nowhere else. A model left unpinned keeps applying
everywhere, the way core does it.
"""

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestDistributionPerJournal(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Model = cls.env["account.analytic.distribution.model"]
        cls.sale_journal = cls.company_data["default_journal_sale"]
        cls.other_journal = cls.sale_journal.copy(
            {"name": "Vanzari interne", "code": "VINT"}
        )
        cls.plan = cls.env["account.analytic.plan"].create({"name": "Proiecte"})
        cls.account_a, cls.account_b = cls.env["account.analytic.account"].create(
            [
                {"name": "Proiect A", "plan_id": cls.plan.id},
                {"name": "Proiect B", "plan_id": cls.plan.id},
            ]
        )

    def _model(self, account, journal=None):
        return self.Model.create(
            {
                "partner_id": self.partner_a.id,
                "journal_id": journal.id if journal else False,
                "analytic_distribution": {str(account.id): 100.0},
            }
        )

    def _distribution(self, journal):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "journal_id": journal.id,
                "invoice_date": "2026-03-15",
                "invoice_line_ids": [
                    (0, 0, {"product_id": self.product_a.id, "price_unit": 100.0})
                ],
            }
        )
        return invoice.invoice_line_ids.analytic_distribution or {}

    def test_a_pinned_model_applies_in_its_own_journal(self):
        self._model(self.account_a, self.sale_journal)
        self.assertEqual(
            self._distribution(self.sale_journal), {str(self.account_a.id): 100.0}
        )

    def test_a_pinned_model_stays_out_of_the_other_journals(self):
        self._model(self.account_a, self.sale_journal)
        self.assertFalse(self._distribution(self.other_journal))

    def test_a_model_with_no_journal_still_applies_everywhere(self):
        """Pinning is opt-in; the models already in use must not change
        behaviour."""
        self._model(self.account_b)
        self.assertEqual(
            self._distribution(self.other_journal), {str(self.account_b.id): 100.0}
        )

    def test_the_pinned_model_wins_over_the_unpinned_one_in_its_journal(self):
        self._model(self.account_b)
        self._model(self.account_a, self.sale_journal)
        self.assertEqual(
            self._distribution(self.sale_journal), {str(self.account_a.id): 100.0}
        )

    def test_the_journal_is_part_of_what_is_searched_on(self):
        """Without it in the defaults, a pinned model would match any line."""
        self.assertIn("journal_id", self.Model._get_default_search_domain_vals())

    def test_the_line_tells_the_engine_which_journal_it_is_in(self):
        """Without it in the arguments, a pinned model would never match."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2026-03-15",
                "invoice_line_ids": [
                    (0, 0, {"product_id": self.product_a.id, "price_unit": 100.0})
                ],
            }
        )
        line = invoice.invoice_line_ids
        self.assertEqual(
            line._get_analytic_distribution_arguments(self.plan)["journal_id"],
            self.sale_journal.id,
        )

    def test_dropping_the_journal_takes_the_models_pinned_to_it(self):
        model = self._model(self.account_a, self.other_journal)
        self.other_journal.unlink()
        self.assertFalse(model.exists())
