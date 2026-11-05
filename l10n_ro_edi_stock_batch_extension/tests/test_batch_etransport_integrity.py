# Copyright 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""A batch ANAF holds a UIT for keeps its goods until the UIT is deleted.

The notification declares exactly the transfers in the batch: while it is
alive the batch cannot be deleted or cancelled and no transfer can be slipped
in or taken out by hand. Odoo's own flows (validating, backorders) still
detach what they need to. ANAF itself is mocked.
"""

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.l10n_ro_edi_stock_extension.tests.test_etransport_integrity import (
    _REQUEST,
    EtransportIntegrityCommon,
    _anaf,
)


@tagged("post_install", "-at_install")
class TestBatchEtransportIntegrity(EtransportIntegrityCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.outgoing_type.auto_batch = False
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.outgoing_type.default_location_src_id, 100
        )

    def _batch(self, count=2):
        pickings = self.env["stock.picking"]
        for _i in range(count):
            pickings |= self._picking()
        return self.env["stock.picking.batch"].create(
            {
                "picking_type_id": self.outgoing_type.id,
                "picking_ids": [(6, 0, pickings.ids)],
            }
        )

    def test_a_batch_never_notified_can_be_cancelled_and_deleted(self):
        batch = self._batch()
        batch.picking_ids[0].batch_id = False
        self.assertEqual(len(batch.picking_ids), 1)
        batch.action_cancel()
        self.assertEqual(batch.state, "cancel")
        batch.unlink()
        self.assertFalse(batch.exists())

    def test_a_batch_being_processed_cannot_be_cancelled_or_deleted(self):
        batch = self._send(self._batch())
        with self.assertRaises(UserError):
            batch.action_cancel()
        with self.assertRaises(UserError):
            batch.unlink()
        self.assertEqual(len(batch.picking_ids), 2)
        with self.assertRaises(UserError):
            batch.l10n_ro_edi_stock_vehicle_number = "TM99XYZ"
        with self.assertRaises(UserError):
            self.env["l10n.ro.edi.stock.document.line"].create(
                {"batch_id": batch.id, "document_date": "2026-11-05"}
            )

    def test_the_declared_transfers_cannot_be_changed_by_hand(self):
        batch = self._validate(self._batch())
        picking = batch.picking_ids[0]
        with self.assertRaises(UserError):
            picking.batch_id = False
        with self.assertRaises(UserError):
            batch.picking_ids = [(3, picking.id)]
        extra = self._picking()
        with self.assertRaises(UserError):
            extra.batch_id = batch
        with self.assertRaises(UserError):
            batch.write({"picking_ids": [(4, extra.id)]})
        with self.assertRaises(UserError):
            picking.unlink()
        self.assertEqual(len(batch.picking_ids), 2)
        self.assertFalse(extra.batch_id)

    def test_a_live_batch_takes_no_auto_batched_transfer(self):
        batch = self._validate(self._batch())
        self.assertFalse(batch._is_picking_auto_mergeable(self._picking()))

    def test_flow_validated_batch_is_delivered_then_holds(self):
        batch = self._validate(self._batch())
        batch.action_confirm()
        batch.action_assign()
        for move in batch.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        batch.action_done()
        self.assertEqual(batch.state, "done")
        self.assertEqual(set(batch.picking_ids.mapped("state")), {"done"})
        self.assertEqual(len(batch.picking_ids), 2)
        with self.assertRaises(UserError):
            batch.unlink()

    def test_flow_validated_batch_released_by_deletion(self):
        batch = self._validate(self._batch())
        with self.assertRaises(UserError):
            batch.action_cancel()
        self._wizard(batch, "delete")
        self.assertEqual(batch.l10n_ro_edi_stock_state, "stock_deleted")
        batch.picking_ids[0].batch_id = False
        batch.action_cancel()
        self.assertEqual(batch.state, "cancel")

    def test_flow_vehicle_change_on_the_batch_keeps_actions_open(self):
        batch = self._validate(self._batch())
        self._wizard(batch, "modify_vehicle", new_vehicle_number="TM01ABC")
        self.assertEqual(batch.l10n_ro_edi_stock_state, "stock_vehicle_modified")
        self.assertEqual(batch.l10n_ro_edi_stock_vehicle_number, "TM01ABC")
        self.assertTrue(batch.l10n_ro_edi_stock_enable_amend)
        self._wizard(batch, "confirm", confirmation_type="10")
        self.assertEqual(batch.l10n_ro_edi_stock_state, "stock_confirmed")
        with self.assertRaises(UserError):
            batch.action_cancel()

    def test_no_action_on_a_batch_anaf_has_not_validated(self):
        batch = self._send(self._batch())
        for action, vals in (
            ("delete", {}),
            ("confirm", {"confirmation_type": "10"}),
            ("modify_vehicle", {"new_vehicle_number": "TM01ABC"}),
        ):
            with self.assertRaises(UserError):
                self._wizard(batch, action, **vals)
        self.assertEqual(len(batch.l10n_ro_edi_stock_document_ids), 1)

    def test_validating_with_a_backorder_still_detaches(self):
        """Odoo's own flow takes the unfinished transfer out of the batch."""
        batch = self._validate(self._batch())
        batch.action_confirm()
        batch.action_assign()
        first, second = batch.picking_ids
        for move in first.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        with patch(_REQUEST, side_effect=_anaf):
            first.button_validate()
        self.assertEqual(first.state, "done")
        self.assertNotEqual(first.batch_id, batch)
        self.assertEqual(second.batch_id, batch)

    def test_a_batch_deletion_waiting_or_refused_keeps_the_batch(self):
        batch = self._validate(self._batch())
        self._wizard(batch, "delete", answer=None)
        self.assertTrue(batch.l10n_ro_edi_stock_enable_fetch)
        with self.assertRaises(UserError):
            batch.action_cancel()
        self._fetch(batch, "nok")
        self.assertEqual(batch.l10n_ro_edi_stock_state, "stock_sending_failed")
        with self.assertRaises(UserError):
            batch.action_cancel()
        with self.assertRaises(UserError):
            batch.picking_ids[0].batch_id = False
        self.assertTrue(batch.l10n_ro_edi_stock_enable_uit_action)
        self._fetch(batch)  # nothing waiting any more
        self._wizard(batch, "delete")
        self.assertEqual(batch.l10n_ro_edi_stock_state, "stock_deleted")
        batch.picking_ids[0].batch_id = False
        batch.action_cancel()
        self.assertEqual(batch.state, "cancel")

    def test_a_batch_vehicle_change_applies_once_accepted(self):
        batch = self._validate(self._batch())
        self._wizard(batch, "modify_vehicle", answer=None, new_vehicle_number="TM01NEW")
        self.assertFalse(batch.l10n_ro_edi_stock_vehicle_number)
        self._fetch(batch, "nok")
        self.assertFalse(batch.l10n_ro_edi_stock_vehicle_number)
        self._wizard(batch, "modify_vehicle", new_vehicle_number="TM01NEW")
        self.assertEqual(batch.l10n_ro_edi_stock_vehicle_number, "TM01NEW")

    def test_a_batch_confirmation_refused_then_accepted(self):
        batch = self._validate(self._batch())
        self._wizard(batch, "confirm", answer="nok", confirmation_type="10")
        self.assertTrue(batch.l10n_ro_edi_stock_enable_uit_action)
        self._wizard(batch, "confirm", confirmation_type="10")
        self.assertEqual(batch.l10n_ro_edi_stock_state, "stock_confirmed")

    def test_the_cron_fetches_waiting_batch_actions(self):
        batch = self._validate(self._batch())
        self._wizard(batch, "confirm", answer=None, confirmation_type="10")
        with patch(_REQUEST, side_effect=_anaf):
            self.env["stock.picking.batch"]._l10n_ro_edi_stock_cron_fetch_status()
        self.assertEqual(batch.l10n_ro_edi_stock_state, "stock_confirmed")
