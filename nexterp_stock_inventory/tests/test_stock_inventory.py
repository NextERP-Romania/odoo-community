# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""The stocktaking document Romanian accounting asks for.

Odoo adjusts quants one by one; here the count is one document, dated, with a
line per quant that keeps both the book quantity and the counted one -- and
the value before and after, which is what goes into the accounts.
"""

from odoo.exceptions import UserError, ValidationError
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

    # ------------------------------------------------------------------
    # Documentul validat ramane cum a fost validat
    # ------------------------------------------------------------------
    def _validated_inventory(self):
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        self._line_for(inventory, self.product1).inventory_quantity = 8
        inventory.action_validate_inventory()
        return inventory

    def test_a_validated_inventory_cannot_be_validated_again(self):
        inventory = self._validated_inventory()
        with self.assertRaises(UserError):
            inventory.action_validate_inventory()
        self.assertEqual(
            self.env["stock.quant"]._get_available_quantity(
                self.product1, self.stock_location
            ),
            8,
        )

    def test_a_validated_inventory_cannot_be_regenerated_or_cleared(self):
        inventory = self._validated_inventory()
        with self.assertRaises(UserError):
            inventory.action_generate_inventory_lines()
        with self.assertRaises(UserError):
            inventory.action_clear_inventory_lines()

    def test_the_count_of_a_validated_inventory_cannot_be_changed(self):
        inventory = self._validated_inventory()
        line = self._line_for(inventory, self.product1)
        with self.assertRaises(UserError):
            line.inventory_quantity = 3
        with self.assertRaises(UserError):
            self.env["l10n.ro.stock.inventory.line"].create(
                {
                    "inventory_id": inventory.id,
                    "location_id": self.stock_location.id,
                    "product_id": self.product2.id,
                    "inventory_quantity": 5,
                }
            )
        with self.assertRaises(UserError):
            inventory.accounting_date = "2026-04-30"
        with self.assertRaises(UserError):
            inventory.state = "draft"

    def test_a_validated_inventory_and_its_lines_cannot_be_deleted(self):
        inventory = self._validated_inventory()
        with self.assertRaises(UserError):
            inventory.inventory_line_ids.unlink()
        with self.assertRaises(UserError):
            inventory.unlink()

    def test_a_draft_inventory_can_be_deleted_with_its_lines(self):
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        lines = inventory.inventory_line_ids
        inventory.unlink()
        self.assertFalse(lines.exists())

    def test_a_counted_line_keeps_its_quant(self):
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        line = self._line_for(inventory, self.product1)
        with self.assertRaises(UserError):
            line.product_id = self.product2

    def test_goods_moved_after_the_count_do_not_block_validation(self):
        """Odoo would open its conflict wizard and apply nothing; the document
        applies the counted quantity and only then is marked done."""
        self._stock(self.product1, 10)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        self._line_for(inventory, self.product1).inventory_quantity = 8
        self._stock(self.product1, 5)
        self.assertTrue(self._line_for(inventory, self.product1).quant_id.is_outdated)
        inventory.action_validate_inventory()
        self.assertEqual(inventory.state, "done")
        line = self._line_for(inventory, self.product1)
        self.assertEqual(line.quantity, 15)
        self.assertEqual(line.inventory_diff_quantity, -7)
        self.assertEqual(
            self.env["stock.quant"]._get_available_quantity(
                self.product1, self.stock_location
            ),
            8,
        )

    def test_an_outdated_quant_adjustment_leaves_no_document_until_settled(self):
        self._stock(self.product1, 10)
        quant = self.env["stock.quant"].search(
            [
                ("product_id", "=", self.product1.id),
                ("location_id", "=", self.stock_location.id),
            ]
        )
        quant.with_context(inventory_mode=True).inventory_quantity = 7
        self.assertEqual(quant.inventory_diff_quantity, -3)
        self._stock(self.product1, 5)
        self.assertTrue(quant.is_outdated)
        res = quant.with_context(inventory_mode=True).action_apply_inventory()
        self.assertEqual(res["res_model"], "stock.inventory.conflict")
        self.assertFalse(self.Inventory.search([]))
        wizard = (
            self.env["stock.inventory.conflict"]
            .with_context(**res["context"])
            .create({})
        )
        # in the UI the wizard runs in a new request, with a fresh cache
        self.env.invalidate_all()
        wizard.action_keep_counted_quantity()
        inventories = self.Inventory.search([])
        self.assertEqual(len(inventories), 1)
        self.assertEqual(inventories.state, "done")
        self.assertEqual(quant.quantity, 7)

    # ------------------------------------------------------------------
    # Fluxul complet
    # ------------------------------------------------------------------
    def test_flow_count_validate_books_the_inventory_moves(self):
        self._stock(self.product1, 10)
        self._stock(self.product2, 4)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        self._line_for(inventory, self.product1).inventory_quantity = 8
        self._line_for(inventory, self.product2).inventory_quantity = 6
        inventory.action_validate_inventory()
        self.assertEqual(inventory.state, "done")
        self.assertEqual(set(inventory.inventory_line_ids.mapped("state")), {"done"})
        moves = self.env["stock.move"].search(
            [
                ("product_id", "in", (self.product1 | self.product2).ids),
                ("is_inventory", "=", True),
            ]
        )
        self.assertEqual(set(moves.mapped("state")), {"done"})
        out_move = moves.filtered(lambda m: m.product_id == self.product1)
        in_move = moves.filtered(lambda m: m.product_id == self.product2)
        self.assertEqual(out_move.quantity, 2)
        self.assertEqual(out_move.location_id, self.stock_location)
        self.assertEqual(out_move.location_dest_id.usage, "inventory")
        self.assertEqual(in_move.quantity, 2)
        self.assertEqual(in_move.location_dest_id, self.stock_location)
        self.assertEqual(
            sum(inventory.inventory_line_ids.mapped("inventory_diff_value")), -10.0
        )

    def test_flow_validated_lines_keep_their_unit(self):
        inventory = self._validated_inventory()
        self.assertEqual(
            self._line_for(inventory, self.product1).product_uom_id,
            self.product1.uom_id,
        )

    def test_flow_draft_lines_stay_editable_and_deletable(self):
        self._stock(self.product1, 10)
        self._stock(self.product2, 4)
        inventory = self._inventory()
        inventory.action_generate_inventory_lines()
        line = self._line_for(inventory, self.product2)
        line.inventory_quantity = 1
        self.assertEqual(line.inventory_diff_quantity, -3)
        line.unlink()
        inventory.accounting_date = "2026-04-30"
        inventory.action_validate_inventory()
        self.assertEqual(inventory.inventory_line_ids.product_id, self.product1)
        self.assertEqual(
            self.env["stock.quant"]._get_available_quantity(
                self.product2, self.stock_location
            ),
            4,
        )

    def test_flow_tracked_goods_need_a_lot_to_be_counted_in(self):
        tracked = self.env["product.product"].create(
            {
                "name": "Produs cu lot",
                "is_storable": True,
                "tracking": "lot",
                "categ_id": self.category.id,
                "standard_price": 2.0,
            }
        )
        inventory = self._inventory()
        with self.assertRaises(ValidationError):
            self.env["l10n.ro.stock.inventory.line"].create(
                {
                    "inventory_id": inventory.id,
                    "location_id": self.stock_location.id,
                    "product_id": tracked.id,
                    "inventory_quantity": 5,
                }
            )
        lot = self.env["stock.lot"].create({"name": "L001", "product_id": tracked.id})
        line = self.env["l10n.ro.stock.inventory.line"].create(
            {
                "inventory_id": inventory.id,
                "location_id": self.stock_location.id,
                "product_id": tracked.id,
                "product_lot_id": lot.id,
                "inventory_quantity": 5,
            }
        )
        inventory.inventory_lines_generated = True
        inventory.action_validate_inventory()
        self.assertEqual(line.quant_id.lot_id, lot)
        self.assertEqual(line.quant_id.quantity, 5)
