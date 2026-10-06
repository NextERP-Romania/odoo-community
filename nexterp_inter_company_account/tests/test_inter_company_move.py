# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Marking the entries booked against another company of the group.

The mark sits on the entry and is carried down to every line, so a report can
leave inter-company turnover out without walking back up to the entry.
"""

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestInterCompanyMove(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.sister = cls.env["res.company"].create({"name": "Firma sora"})

    def _invoice(self, partner):
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "invoice_date": "2026-03-15",
                "invoice_line_ids": [
                    (0, 0, {"product_id": self.product_a.id, "price_unit": 100.0})
                ],
            }
        )

    def test_an_invoice_to_a_company_of_the_group_is_marked(self):
        self.assertTrue(self._invoice(self.sister.partner_id).is_inter_company)

    def test_an_invoice_to_an_outside_customer_is_not(self):
        self.assertFalse(self._invoice(self.partner_a).is_inter_company)

    def test_an_invoice_to_our_own_partner_is_not_inter_company(self):
        """It is the same company on both sides; there is nothing between."""
        self.assertFalse(self._invoice(self.company.partner_id).is_inter_company)

    def test_a_contact_is_judged_by_the_company_it_belongs_to(self):
        contact = self.env["res.partner"].create(
            {"name": "Persoana", "parent_id": self.sister.partner_id.id}
        )
        self.assertTrue(self._invoice(contact).is_inter_company)

    def test_the_mark_is_carried_down_to_the_lines(self):
        invoice = self._invoice(self.sister.partner_id)
        self.assertTrue(all(invoice.line_ids.mapped("is_inter_company")))

    def test_changing_the_customer_changes_the_mark(self):
        invoice = self._invoice(self.partner_a)
        invoice.partner_id = self.sister.partner_id
        self.assertTrue(invoice.is_inter_company)
        self.assertTrue(all(invoice.line_ids.mapped("is_inter_company")))
