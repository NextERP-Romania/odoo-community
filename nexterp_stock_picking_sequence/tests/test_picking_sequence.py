# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPickingSequence(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write(
            {
                "stock_assign_number_in_process": True,
                "draft_picking_sequence_id": cls.env.ref(
                    "nexterp_stock_picking_sequence.sequence_draft_picking"
                ).id,
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.picking_type = cls.warehouse.int_type_id
        cls.product = cls.env["product.product"].create(
            {"name": "Produs numerotare (test)", "is_storable": True}
        )
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.warehouse.lot_stock_id, 10
        )

    def _picking(self):
        return self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.warehouse.lot_stock_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "location_id": self.warehouse.lot_stock_id.id,
                            "location_dest_id": self.warehouse.lot_stock_id.id,
                        },
                    )
                ],
            }
        )

    def _next(self, sequence):
        # the standard implementation counts in a PostgreSQL sequence: the
        # computed field has to be read again, not from the cache
        sequence.invalidate_recordset(["number_next_actual"])
        return sequence.number_next_actual

    def _validate(self, picking):
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.picked = True
        picking.button_validate()

    def test_draft_name_then_number_at_validation(self):
        sequence = self.picking_type.sequence_id
        before = self._next(sequence)
        picking = self._picking()
        self.assertTrue(picking.name.startswith("Draft-"))
        self.assertEqual(self._next(sequence), before)
        self._validate(picking)
        self.assertEqual(picking.state, "done")
        self.assertTrue(picking.name.startswith(sequence.prefix or ""))
        self.assertFalse(picking.name.startswith("Draft-"))
        self.assertEqual(self._next(sequence), before + 1)

    def test_cancelled_transfer_leaves_no_gap(self):
        sequence = self.picking_type.sequence_id
        cancelled = self._picking()
        cancelled.action_cancel()
        before = self._next(sequence)
        done = self._picking()
        self._validate(done)
        self.assertEqual(self._next(sequence), before + 1)
        self.assertTrue(cancelled.name.startswith("Draft-"))

    def test_setting_off_keeps_the_standard_numbering(self):
        self.company.stock_assign_number_in_process = False
        picking = self._picking()
        self.assertFalse(picking.name.startswith("Draft-"))
