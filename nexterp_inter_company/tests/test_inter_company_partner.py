# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Telling the group's own companies apart from outside customers.

A partner that stands for one of the companies in the database is marked, so
anything booked against it can later be left out of consolidated figures.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestInterCompanyPartner(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sister = cls.env["res.company"].create({"name": "Firma sora"})
        cls.outsider = cls.env["res.partner"].create({"name": "Client din afara"})

    def test_the_partner_of_a_company_is_marked(self):
        self.assertTrue(self.sister.partner_id.is_inter_company)

    def test_an_outside_partner_is_not(self):
        self.assertFalse(self.outsider.is_inter_company)

    def test_a_new_company_marks_its_own_partner(self):
        company = self.env["res.company"].create({"name": "Firma noua"})
        self.assertTrue(company.partner_id.is_inter_company)

    def test_the_mark_can_be_set_by_hand(self):
        """The compute is not readonly: a partner that stands for a company
        kept outside this database is marked by the accountant."""
        self.outsider.is_inter_company = True
        self.assertTrue(self.outsider.is_inter_company)

    def test_a_contact_of_a_company_partner_is_not_marked_itself(self):
        contact = self.env["res.partner"].create(
            {"name": "Persoana", "parent_id": self.sister.partner_id.id}
        )
        self.assertFalse(contact.is_inter_company)

    def test_a_company_that_changes_its_partner_moves_the_mark(self):
        old = self.sister.partner_id
        self.sister.partner_id = self.outsider
        self.assertTrue(self.outsider.is_inter_company)
        self.assertFalse(old.is_inter_company)
