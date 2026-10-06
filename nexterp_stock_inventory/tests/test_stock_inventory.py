# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""The stocktaking document Romanian accounting asks for.

Odoo adjusts quants one by one; here the count is one document, dated, with a
line per quant that keeps both the book quantity and the counted one -- and
the value before and after, which is what goes into the accounts.
"""

from odoo.tests import tagged

from odoo.addons.stock_account.tests.common import TestStockValuationCommon


@tagged("post_install", "-at_install")
class TestStockInventory(TestStockValuationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Inventory = cls.env["l10n.ro.stock.inventory"]
        cls.category = cls.env["product.category"].create(
            {
                "name": "Marfa la pret standard",
                "property_cost_method": "standard",
                "property_valuation": "real_time",
            }
        )
        cls.product1, cls.product2 = cls.env["product.product"].create(
            [
                {
                    "name": "Produs 1",
                    "is_storable": True,
                    "categ_id": cls.category.id,
                    "standard_price": 10.0,
                },
                {
                    "name": "Produs 2",
                    "is_storable": True,
                    "categ_id": cls.category.id,
                    "standard_price": 5.0,
                },
            ]
        )

    def _stock(self, product, qty, location=None):
        self.env["stock.quant"]._update_available_quantity(
            product, location or self.stock_location, qty
        )

    def _inventory(self, **vals):
        return self.Inventory.create({"accounting_date": "2026-03-31", **vals})

    def _line_for(self, inventory, product):
        return inventory.inventory_line_ids.filtered(
            lambda line: line.product_id == product
        )

    # ------------------------------------------------------------------
    # Documentul
    # ------------------------------------------------------------------
    def test_the_document_is_named_after_the_day_it_is_dated(self):
        self.assertEqual(self._inventory().name, "Inventory - 2026-03-31")

    def test_a_new_inventory_starts_in_draft_with_no_lines(self):
        inventory = self._inventory()
        self.assertEqual(inventory.state, "draft")
        self.assertFalse(inventory.inventory_lines_generated)
        self.assertFalse(inventory.inventory_line_ids)

    # ------------------------------------------------------------------
    # Generarea liniilor
    # ------------------------------------------------------------------
    def test_generating_brings_in_a_line_per_quant_on_hand(self):
        self._stock(self.product1, 10)
        self._stock(self.product2, 4)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        self.assertTrue(inventory.inventory_lines_generated)
        self.assertEqual(
            set(inventory.inventory_line_ids.mapped("product_id")),
            {self.product1, self.product2},
        )

    def test_the_line_keeps_the_book_quantity_and_its_value(self):
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        line = self._line_for(inventory, self.product1)
        self.assertEqual(line.quantity, 10)
        self.assertEqual(line.value, 100.0)
        self.assertEqual(line.standard_price, 10.0)

    def test_naming_the_products_narrows_the_count_to_them(self):
        self._stock(self.product1, 10)
        self._stock(self.product2, 4)
        inventory = self._inventory(product_ids=[(6, 0, self.product1.ids)])
        inventory.action_generate_inventory_lines()
        self.assertEqual(inventory.inventory_line_ids.product_id, self.product1)

    def test_naming_the_locations_narrows_the_count_to_them(self):
        other = self.env["stock.location"].create(
            {
                "name": "Depozit 2",
                "usage": "internal",
                "location_id": self.stock_location.location_id.id,
            }
        )
        self._stock(self.product1, 10)
        self._stock(self.product2, 4, location=other)
        inventory = self._inventory(location_ids=[(6, 0, other.ids)])
        inventory.action_generate_inventory_lines()
        self.assertEqual(inventory.inventory_line_ids.product_id, self.product2)

    def test_generating_twice_does_not_duplicate_a_line(self):
        """The count takes days; new goods arrive meanwhile and the document
        has to be refreshed without losing what was already counted."""
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        self._line_for(inventory, self.product1).inventory_quantity = 8
        self._stock(self.product2, 4)
        inventory.action_generate_inventory_lines()
        self.assertEqual(len(inventory.inventory_line_ids), 2)
        self.assertEqual(self._line_for(inventory, self.product1).inventory_quantity, 8)

    def test_clearing_takes_the_lines_away(self):
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        inventory.action_clear_inventory_lines()
        self.assertFalse(inventory.inventory_line_ids)
        self.assertFalse(inventory.inventory_lines_generated)

    def test_the_same_quant_cannot_be_counted_twice_on_one_document(self):
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        quant = inventory.inventory_line_ids.quant_id
        before = len(inventory.inventory_line_ids)
        inventory.action_generate_inventory_lines(quants=quant)
        self.assertEqual(len(inventory.inventory_line_ids), before)

    # ------------------------------------------------------------------
    # Numararea
    # ------------------------------------------------------------------
    def test_counting_less_than_the_books_shows_the_shortfall(self):
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        line = self._line_for(inventory, self.product1)
        line.inventory_quantity = 8
        self.assertEqual(line.inventory_diff_quantity, -2)

    def test_counting_more_than_the_books_shows_the_surplus(self):
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        line = self._line_for(inventory, self.product1)
        line.inventory_quantity = 12
        self.assertEqual(line.inventory_diff_quantity, 2)

    def test_a_line_typed_by_hand_finds_or_opens_its_quant(self):
        """Goods that are on the shelf but not in Odoo still have to be
        counted."""
        inventory = self._inventory()
        line = self.env["l10n.ro.stock.inventory.line"].create(
            {
                "inventory_id": inventory.id,
                "location_id": self.stock_location.id,
                "product_id": self.product1.id,
                "inventory_quantity": 5,
            }
        )
        self.assertTrue(line.quant_id)
        self.assertEqual(line.quant_id.product_id, self.product1)
        self.assertEqual(line.quant_id.location_id, self.stock_location)

    # ------------------------------------------------------------------
    # Validarea
    # ------------------------------------------------------------------
    def test_validating_writes_the_count_into_the_stock(self):
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        self._line_for(inventory, self.product1).inventory_quantity = 8
        inventory.action_validate_inventory()
        self.assertEqual(inventory.state, "done")
        self.assertEqual(
            self.env["stock.quant"]._get_available_quantity(
                self.product1, self.stock_location
            ),
            8,
        )

    def test_validating_records_the_value_before_and_after(self):
        """That difference is the amount that is booked."""
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        self._line_for(inventory, self.product1).inventory_quantity = 8
        inventory.action_validate_inventory()
        line = self._line_for(inventory, self.product1)
        self.assertEqual(line.value, 100.0)
        self.assertEqual(line.inventory_value, 80.0)
        self.assertEqual(line.inventory_diff_value, -20.0)

    def test_validating_does_not_open_a_second_document(self):
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        self._line_for(inventory, self.product1).inventory_quantity = 8
        inventory.action_validate_inventory()
        self.assertEqual(self.Inventory.search_count([]), 1)

    # ------------------------------------------------------------------
    # Ajustarile facute pe langa document
    # ------------------------------------------------------------------
    def test_an_adjustment_made_on_the_quant_gets_its_own_document(self):
        """Nothing may change the stock without leaving a stocktaking
        document behind."""
        self._stock(self.product1, 10)
        quant = self.env["stock.quant"].search(
            [
                ("product_id", "=", self.product1.id),
                ("location_id", "=", self.stock_location.id),
            ]
        )
        quant.with_context(inventory_mode=True).inventory_quantity = 7
        quant.with_context(inventory_mode=True).action_apply_inventory()
        inventory = self.Inventory.search([], limit=1)
        self.assertTrue(inventory)
        self.assertEqual(inventory.state, "done")
        self.assertEqual(self._line_for(inventory, self.product1).quantity, 10)

    def test_the_document_made_for_an_adjustment_carries_its_values(self):
        self._stock(self.product1, 10)
        quant = self.env["stock.quant"].search(
            [
                ("product_id", "=", self.product1.id),
                ("location_id", "=", self.stock_location.id),
            ]
        )
        quant.with_context(inventory_mode=True).inventory_quantity = 7
        quant.with_context(inventory_mode=True).action_apply_inventory()
        line = self.Inventory.search([], limit=1).inventory_line_ids
        self.assertEqual(line.value, 100.0)
        self.assertEqual(line.inventory_value, 70.0)
        self.assertEqual(line.inventory_diff_value, -30.0)
