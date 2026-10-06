# Copyright 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Changing the pricelist on a quotation that already has lines.

Core only offers a button; with the setting on the prices are recomputed as
soon as the pricelist changes, and the change is written in the chatter so it
is clear why the figures moved.
"""

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase


@tagged("post_install", "-at_install")
class TestAutoUpdatePrice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        # The pricelist only shows on the quotation when pricelists are in
        # use, and a field that does not show cannot be changed on the form.
        cls.env.user.group_ids += cls.env.ref("product.group_product_pricelist")
        cls.partner = cls.env["res.partner"].create({"name": "Client"})
        cls.product = cls.env["product.product"].create(
            {"name": "Marfa", "list_price": 100.0, "type": "consu"}
        )
        cls.currency = cls.company.currency_id
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "Lista standard", "currency_id": cls.currency.id}
        )
        cls.discounted = cls.env["product.pricelist"].create(
            {
                "name": "Lista cu discount",
                "currency_id": cls.currency.id,
                "item_ids": [
                    Command.create(
                        {
                            "compute_price": "percentage",
                            "percent_price": 20,
                            "applied_on": "3_global",
                        }
                    )
                ],
            }
        )

    def _order(self):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "order_line": [
                    Command.create(
                        {"product_id": self.product.id, "product_uom_qty": 1}
                    )
                ],
            }
        )

    def _switch_pricelist(self, order):
        form = Form(order)
        form.pricelist_id = self.discounted
        return form.save()

    def test_without_the_setting_the_price_waits_for_the_button(self):
        order = self._order()
        self.assertEqual(self._switch_pricelist(order).order_line.price_unit, 100.0)

    def test_with_the_setting_on_the_price_follows_the_pricelist(self):
        self.company.sale_auto_update_price = True
        order = self._order()
        self.assertEqual(self._switch_pricelist(order).order_line.price_unit, 80.0)

    def test_the_change_is_written_in_the_chatter(self):
        """The figures moved on their own, so the quotation has to say why."""
        self.company.sale_auto_update_price = True
        order = self._order()
        before = len(order.message_ids)
        self._switch_pricelist(order)
        bodies = order.message_ids[: len(order.message_ids) - before].mapped("body")
        self.assertTrue(any("Lista cu discount" in body for body in bodies))

    def test_an_empty_quotation_has_nothing_to_recompute(self):
        self.company.sale_auto_update_price = True
        order = self.env["sale.order"].create(
            {"partner_id": self.partner.id, "pricelist_id": self.pricelist.id}
        )
        self._switch_pricelist(order)
        self.assertFalse(order.order_line)

    def test_the_setting_follows_the_company(self):
        self.assertFalse(
            self.env["res.config.settings"].create({}).sale_auto_update_price
        )
        self.company.sale_auto_update_price = True
        self.assertTrue(
            self.env["res.config.settings"].create({}).sale_auto_update_price
        )
