# Copyright 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""When validating a transfer asks for a delivery carrier.

The base module asks for one on every receipt and delivery of a Romanian
company, even when nobody means to send it to eTransport. Here the carrier is
only asked for once the transfer has an eTransport operation type.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEtransportCarrier(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.account_fiscal_country_id = cls.env.ref("base.ro")
        cls.partner = cls.env["res.partner"].create({"name": "Client"})
        cls.product = cls.env["product.product"].create(
            {"name": "Marfa", "type": "consu"}
        )
        cls.outgoing_type = cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", cls.company.id)], limit=1
        )
        cls.transporter = cls.env["res.partner"].create({"name": "Transportator"})
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Curier",
                "product_id": cls.env["product.product"]
                .create({"name": "Livrare", "type": "service"})
                .id,
                "l10n_ro_edi_stock_partner_id": cls.transporter.id,
            }
        )

    def _picking(self, **vals):
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.outgoing_type.id,
                "location_id": self.outgoing_type.default_location_src_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 1})
                ],
                **vals,
            }
        )
        picking.action_confirm()
        picking.move_ids.write({"quantity": 1, "picked": True})
        return picking

    def test_the_transfer_is_in_scope_for_etransport(self):
        """Guard: without this the other tests would pass for the wrong
        reason (the base check is skipped outside Romania)."""
        self.assertTrue(self._picking().l10n_ro_edi_stock_enable)

    def test_a_delivery_not_meant_for_etransport_validates_without_a_carrier(self):
        picking = self._picking()
        picking.button_validate()
        self.assertEqual(picking.state, "done")

    def test_a_delivery_meant_for_etransport_still_needs_a_carrier(self):
        picking = self._picking(l10n_ro_edi_stock_operation_type="30")
        with self.assertRaisesRegex(UserError, "missing a delivery carrier"):
            picking.button_validate()

    def test_the_carrier_still_needs_its_transport_company(self):
        self.carrier.l10n_ro_edi_stock_partner_id = False
        picking = self._picking(
            l10n_ro_edi_stock_operation_type="30", carrier_id=self.carrier.id
        )
        with self.assertRaisesRegex(UserError, "missing the partner field value"):
            picking.button_validate()

    def test_a_delivery_meant_for_etransport_validates_with_a_carrier(self):
        picking = self._picking(
            l10n_ro_edi_stock_operation_type="30", carrier_id=self.carrier.id
        )
        picking.button_validate()
        self.assertEqual(picking.state, "done")

    def test_a_transfer_outside_romania_is_never_checked(self):
        self.company.account_fiscal_country_id = self.env.ref("base.be")
        picking = self._picking(l10n_ro_edi_stock_operation_type="30")
        self.assertFalse(picking._l10n_ro_edi_stock_validate_carrier_filter(picking))

    def test_a_batch_still_forces_the_carrier_check(self):
        """l10n_ro_edi_stock_batch validates the pickings of a batch with
        l10n_ro_edi_stock_validate_carrier in the context. The eTransport
        operation type lives on the batch, not on its pickings, so the check
        must not depend on the picking's operation type there."""
        batch_fields = self.env["stock.picking.batch"]._fields
        if "l10n_ro_edi_stock_operation_type" not in batch_fields:
            self.skipTest("l10n_ro_edi_stock_batch is not installed")
        picking = self._picking()
        Picking = self.env["stock.picking"].with_context(
            l10n_ro_edi_stock_validate_carrier=True
        )
        self.assertTrue(Picking._l10n_ro_edi_stock_validate_carrier_filter(picking))
