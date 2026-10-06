# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""A kit is priced by what is in it.

The kit itself carries no price of its own: its sales price and its cost are
the sum of its components, so changing a component moves the kit with it.
"""

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductKit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.frame = cls._product("Rama", list_price=60.0, standard_price=30.0)
        cls.glass = cls._product("Sticla", list_price=20.0, standard_price=8.0)
        cls.kit = cls._product("Tablou", list_price=999.0, standard_price=999.0)
        cls.kit.kit_product_ids = [
            Command.create({"component_product_id": cls.frame.id, "product_qty": 1}),
            Command.create({"component_product_id": cls.glass.id, "product_qty": 2}),
        ]

    @classmethod
    def _product(cls, name, **vals):
        return cls.env["product.product"].create(
            {"name": name, "type": "consu", **vals}
        )

    # ------------------------------------------------------------------
    # Linia de kit
    # ------------------------------------------------------------------
    def test_a_kit_line_is_worth_its_quantity_times_the_component(self):
        line = self.kit.kit_product_ids.filtered(
            lambda line: line.component_product_id == self.glass
        )
        self.assertEqual(line.product_price, 40.0)

    def test_a_dearer_component_lifts_the_line(self):
        self.glass.list_price = 25.0
        line = self.kit.kit_product_ids.filtered(
            lambda line: line.component_product_id == self.glass
        )
        self.assertEqual(line.product_price, 50.0)

    def test_the_line_is_named_after_both_products(self):
        line = self.kit.kit_product_ids.filtered(
            lambda line: line.component_product_id == self.frame
        )
        self.assertEqual(line.display_name, f"{self.kit.display_name} - Rama")

    def test_the_line_takes_the_unit_of_its_component(self):
        line = self.kit.kit_product_ids[0]
        self.assertEqual(line.product_uom_id, line.component_product_id.uom_id)

    # ------------------------------------------------------------------
    # Pretul kitului
    # ------------------------------------------------------------------
    def test_the_sales_price_of_a_kit_is_the_sum_of_its_parts(self):
        """Whatever is typed on the kit itself does not count."""
        self.assertEqual(self.kit.lst_price, 100.0)

    def test_the_sales_price_follows_a_component(self):
        self.glass.list_price = 30.0
        self.assertEqual(self.kit.lst_price, 120.0)

    def test_the_sales_price_follows_a_changed_quantity(self):
        self.kit.kit_product_ids.filtered(
            lambda line: line.component_product_id == self.glass
        ).product_qty = 3
        self.assertEqual(self.kit.lst_price, 120.0)

    def test_the_cost_of_a_kit_is_the_sum_of_the_costs(self):
        self.assertEqual(self.kit._price_compute("standard_price")[self.kit.id], 46.0)

    def test_a_product_that_is_not_a_kit_keeps_its_own_price(self):
        self.assertEqual(self.frame.lst_price, 60.0)
        self.assertEqual(
            self.frame._price_compute("standard_price")[self.frame.id], 30.0
        )

    def test_an_emptied_kit_falls_back_to_its_own_price(self):
        self.kit.kit_product_ids.unlink()
        self.assertEqual(self.kit.lst_price, 999.0)

    # ------------------------------------------------------------------
    # Componentele
    # ------------------------------------------------------------------
    def test_a_component_is_taken_off_the_price_list(self):
        """It is only sold inside the kit."""
        self.glass.is_kit_component = True
        self.glass._onchange_is_kit_component()
        self.assertFalse(self.glass.sale_ok)

    def test_the_flag_reaches_the_template(self):
        self.glass.is_kit_component = True
        self.assertTrue(self.glass.product_tmpl_id.is_kit_component)

    def test_the_kit_lines_are_reachable_from_the_template(self):
        self.assertEqual(
            self.kit.product_tmpl_id.kit_product_ids, self.kit.kit_product_ids
        )


@tagged("post_install", "-at_install")
class TestKitOnPricelist(TransactionCase):
    """What a pricelist works from.

    The kit has no sales price of its own, so the pricelist applies its rules
    to the sum of the components -- a rule on the kit discounts that sum, a
    rule on a component does not reach it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.frame = cls.env["product.product"].create(
            {"name": "Rama", "type": "consu", "list_price": 60.0}
        )
        cls.glass = cls.env["product.product"].create(
            {"name": "Sticla", "type": "consu", "list_price": 20.0}
        )
        cls.kit = cls.env["product.product"].create(
            {
                "name": "Tablou",
                "type": "consu",
                "list_price": 999.0,
                "kit_product_ids": [
                    Command.create(
                        {"component_product_id": cls.frame.id, "product_qty": 1}
                    ),
                    Command.create(
                        {"component_product_id": cls.glass.id, "product_qty": 2}
                    ),
                ],
            }
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "Lista", "currency_id": cls.env.company.currency_id.id}
        )

    def _price(self, product, qty=1):
        return self.pricelist._get_product_price(product, qty)

    def test_the_kit_is_priced_from_its_components(self):
        self.assertEqual(self._price(self.kit), 100.0)

    def test_the_price_is_per_kit_whatever_the_quantity(self):
        self.assertEqual(self._price(self.kit, 3), 100.0)

    def test_a_rule_on_the_kit_discounts_the_sum_of_its_parts(self):
        self.pricelist.item_ids = [
            Command.create(
                {
                    "applied_on": "0_product_variant",
                    "product_id": self.kit.id,
                    "compute_price": "discount",
                    "price_discount": 10,
                }
            )
        ]
        self.assertEqual(self._price(self.kit), 90.0)

    def test_a_fixed_rule_on_the_kit_replaces_that_sum(self):
        self.pricelist.item_ids = [
            Command.create(
                {
                    "applied_on": "0_product_variant",
                    "product_id": self.kit.id,
                    "compute_price": "fixed",
                    "fixed_price": 10.0,
                }
            )
        ]
        self.assertEqual(self._price(self.kit), 10.0)

    def test_a_dearer_component_lifts_the_price_of_the_kit(self):
        self.glass.list_price = 30.0
        self.assertEqual(self._price(self.kit), 120.0)

    def test_a_plain_product_is_priced_the_usual_way(self):
        self.assertEqual(self._price(self.frame), 60.0)
