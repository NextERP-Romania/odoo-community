# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Selling a kit: one line for the customer, one detail line per component.

The customer sees the kit, the back office sees what it is made of. The kit's
unit price is whatever the detail lines add up to, so editing a detail line
moves the price the customer is quoted.
"""

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestKitOnSaleOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Client"})
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "Lista", "currency_id": cls.env.company.currency_id.id}
        )
        cls.frame = cls._product("Rama", 60.0)
        cls.glass = cls._product("Sticla", 20.0)
        cls.plain = cls._product("Cui", 5.0)
        cls.kit = cls._product("Tablou", 999.0)
        cls.kit.kit_product_ids = [
            Command.create({"component_product_id": cls.frame.id, "product_qty": 1}),
            Command.create({"component_product_id": cls.glass.id, "product_qty": 2}),
        ]

    @classmethod
    def _product(cls, name, list_price):
        return cls.env["product.product"].create(
            {"name": name, "type": "consu", "list_price": list_price}
        )

    def _order(self, product=None, qty=1):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": (product or self.kit).id,
                            "product_uom_qty": qty,
                        }
                    )
                ],
            }
        )

    # ------------------------------------------------------------------
    # Generarea liniilor de detaliu
    # ------------------------------------------------------------------
    def test_selling_a_kit_writes_down_what_is_in_it(self):
        order = self._order()
        self.assertEqual(
            set(order.kit_line_ids.mapped("product_id")), {self.frame, self.glass}
        )

    def test_a_plain_product_gets_no_detail_lines(self):
        self.assertFalse(self._order(self.plain).kit_line_ids)

    def test_the_detail_lines_hang_off_the_line_that_sold_the_kit(self):
        order = self._order()
        self.assertEqual(order.kit_line_ids.sale_line_id, order.order_line)
        self.assertEqual(order.order_line.kit_line_ids, order.kit_line_ids)

    def test_two_kits_sold_means_twice_the_components(self):
        order = self._order(qty=2)
        glass_line = order.kit_line_ids.filtered(
            lambda line: line.product_id == self.glass
        )
        self.assertEqual(glass_line.product_uom_qty, 4)

    # ------------------------------------------------------------------
    # Pretul
    # ------------------------------------------------------------------
    def test_the_kit_is_quoted_at_what_its_parts_add_up_to(self):
        """What is typed on the kit product itself does not reach the
        customer."""
        self.assertEqual(self._order().order_line.price_unit, 100.0)

    def test_the_quoted_price_is_per_kit_not_per_order(self):
        self.assertEqual(self._order(qty=2).order_line.price_unit, 100.0)

    def test_each_component_is_priced_on_its_own(self):
        order = self._order()
        glass_line = order.kit_line_ids.filtered(
            lambda line: line.product_id == self.glass
        )
        self.assertEqual(glass_line.price_unit, 20.0)
        self.assertEqual(glass_line.price_subtotal, 40.0)

    def test_editing_a_detail_line_moves_the_price_the_customer_sees(self):
        order = self._order()
        glass_line = order.kit_line_ids.filtered(
            lambda line: line.product_id == self.glass
        )
        glass_line.price_unit = 30.0
        self.assertEqual(order.order_line.price_unit, 120.0)

    def test_dropping_a_component_from_the_quote_lowers_the_price(self):
        order = self._order()
        order.kit_line_ids.filtered(
            lambda line: line.product_id == self.glass
        ).product_uom_qty = 0
        self.assertEqual(order.order_line.price_unit, 60.0)

    # ------------------------------------------------------------------
    # Reluarea si curatenia
    # ------------------------------------------------------------------
    def test_changing_the_product_on_the_line_redoes_the_detail(self):
        order = self._order()
        order.write(
            {
                "order_line": [
                    Command.update(order.order_line.id, {"product_id": self.plain.id})
                ]
            }
        )
        self.assertFalse(order.kit_line_ids)

    def test_a_reread_kit_does_not_leave_the_old_detail_behind(self):
        order = self._order()
        order.order_line.with_context(
            change_from_soline=True
        ).generate_sale_order_line_kit()
        self.assertEqual(len(order.kit_line_ids), 2)

    def test_deleting_the_line_takes_its_detail_with_it(self):
        order = self._order()
        order.order_line.unlink()
        self.assertFalse(order.kit_line_ids)

    def test_a_second_kit_line_keeps_its_own_detail(self):
        order = self._order()
        order.write(
            {
                "order_line": [
                    Command.create({"product_id": self.kit.id, "product_uom_qty": 1})
                ]
            }
        )
        self.assertEqual(len(order.kit_line_ids), 4)
        for line in order.order_line:
            self.assertEqual(len(line.kit_line_ids), 2)

    def test_an_order_without_a_pricelist_still_prices_the_components(self):
        """Not every database has pricelists turned on."""
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create({"product_id": self.kit.id, "product_uom_qty": 1})
                ],
            }
        )
        self.assertFalse(order.pricelist_id)
        self.assertEqual(order.order_line.price_unit, 100.0)
