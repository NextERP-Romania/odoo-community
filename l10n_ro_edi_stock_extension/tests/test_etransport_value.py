# Copyright 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""The value and the quantity declared to ANAF for each line of goods.

ANAF asks for a VAT-excluded value in lei. Which price that is depends on
what the movement is: goods coming in are worth their cost, goods going out
are worth what they were sold for. Anything in another currency is converted.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEtransportValue(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Partener"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Marfa",
                "is_storable": True,
                "standard_price": 40.0,
                "list_price": 100.0,
            }
        )
        cls.outgoing_type = cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", cls.company.id)], limit=1
        )
        cls.incoming_type = cls.env["stock.picking.type"].search(
            [("code", "=", "incoming"), ("company_id", "=", cls.company.id)], limit=1
        )

    def _picking(self, picking_type=None, **vals):
        picking_type = picking_type or self.outgoing_type
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id
                or self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": picking_type.default_location_dest_id.id
                or self.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 5,
                        },
                    )
                ],
                **vals,
            }
        )
        picking.action_confirm()
        return picking

    def _value(self, picking, op_type):
        return picking._l10n_ro_edi_stock_compute_value(picking.move_ids, op_type)

    # ------------------------------------------------------------------
    # Sursa aleasa automat
    # ------------------------------------------------------------------
    def test_goods_going_out_are_worth_their_selling_price(self):
        picking = self._picking()
        self.assertEqual(self._value(picking, "20"), 100.0)

    def test_goods_coming_in_are_worth_their_cost(self):
        picking = self._picking(self.incoming_type)
        self.assertEqual(self._value(picking, "10"), 40.0)

    def test_a_national_delivery_is_worth_its_selling_price(self):
        picking = self._picking()
        self.assertEqual(self._value(picking, "30"), 100.0)

    def test_a_national_receipt_is_worth_its_cost(self):
        picking = self._picking(self.incoming_type)
        self.assertEqual(self._value(picking, "30"), 40.0)

    # ------------------------------------------------------------------
    # Sursa aleasa de om
    # ------------------------------------------------------------------
    def test_the_cost_can_be_asked_for_on_a_delivery(self):
        picking = self._picking(l10n_ro_edi_stock_price_source="cost")
        self.assertEqual(self._value(picking, "20"), 40.0)

    def test_the_list_price_can_be_asked_for(self):
        picking = self._picking(
            self.incoming_type, l10n_ro_edi_stock_price_source="list"
        )
        self.assertEqual(self._value(picking, "10"), 100.0)

    def test_a_product_without_a_cost_falls_back_to_the_purchase_order(self):
        """A notification with a zero value is rejected, so an empty cost has
        to find a price somewhere."""
        self.product.standard_price = 0.0
        picking = self._picking(
            self.incoming_type, l10n_ro_edi_stock_price_source="cost"
        )
        self.assertEqual(self._value(picking, "10"), 0.0)

    def test_without_a_sale_order_the_list_price_stands_in(self):
        picking = self._picking(l10n_ro_edi_stock_price_source="sale")
        self.assertEqual(self._value(picking, "20"), 100.0)

    # ------------------------------------------------------------------
    # Cantitatea si unitatea
    # ------------------------------------------------------------------
    def test_the_quantity_and_the_unit_are_reported_in_the_same_unit(self):
        """The base module mixed the two, sending a converted quantity with
        the code of the unit it was converted from."""
        picking = self._picking()
        qty, code = picking._l10n_ro_edi_stock_get_qty_and_uom(picking.move_ids)
        self.assertEqual(qty, 5)
        self.assertEqual(code, picking.move_ids.uom_id._get_unece_code()[:3])

    def test_the_unit_code_is_never_longer_than_anaf_accepts(self):
        picking = self._picking()
        _qty, code = picking._l10n_ro_edi_stock_get_qty_and_uom(picking.move_ids)
        self.assertLessEqual(len(code), 3)

    # ------------------------------------------------------------------
    # Cand se poate trimite
    # ------------------------------------------------------------------
    def test_a_transfer_can_be_notified_before_the_goods_move(self):
        """ANAF has to be told before the lorry leaves, not after."""
        picking = self._picking()
        picking.l10n_ro_edi_stock_enable = True
        picking.invalidate_recordset(["l10n_ro_edi_stock_enable_send"])
        self.assertEqual(picking.state, "confirmed")
        self.assertTrue(picking.l10n_ro_edi_stock_enable_send)

    def test_a_cancelled_transfer_cannot_be_notified(self):
        picking = self._picking()
        picking.l10n_ro_edi_stock_enable = True
        picking.action_cancel()
        self.assertFalse(picking.l10n_ro_edi_stock_enable_send)

    def test_a_transfer_outside_etransport_is_not_offered_the_button(self):
        picking = self._picking()
        picking.l10n_ro_edi_stock_enable = False
        self.assertFalse(picking.l10n_ro_edi_stock_enable_send)
