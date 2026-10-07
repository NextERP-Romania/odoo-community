# Copyright 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""eTransport for a batch of transfers.

A lorry that carries several transfers files one notification for the lot,
not one per transfer. The batch has to answer the same questions a single
transfer does -- what the goods are worth, whose address is at each end --
and the transfers inside it must not file a second UIT for the same goods.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestBatchEtransport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.account_fiscal_country_id = cls.env.ref("base.ro")
        cls.partner = cls.env["res.partner"].create({"name": "Client"})
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

    def _picking(self, picking_type=None):
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
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 5})
                ],
            }
        )
        picking.action_confirm()
        return picking

    def _batch(self, pickings=None, **vals):
        pickings = pickings or self._picking()
        picking_type = pickings[:1].picking_type_id
        return self.env["stock.picking.batch"].create(
            {
                "picking_type_id": picking_type.id,
                "picking_ids": [(6, 0, pickings.ids)],
                **vals,
            }
        )

    # ------------------------------------------------------------------
    # Cine poate trimite notificarea
    # ------------------------------------------------------------------
    def test_a_transfer_in_a_batch_can_still_notify_before_it_moves(self):
        """The whole point of the extension is to tell ANAF before the goods
        leave; the base module silences every transfer that sits in a batch."""
        picking = self._picking()
        self._batch(picking)
        picking.invalidate_recordset(["l10n_ro_edi_stock_enable"])
        self.assertTrue(picking.l10n_ro_edi_stock_enable)

    def test_once_the_batch_has_filed_the_transfers_go_quiet(self):
        """Two UIT for the same goods would be a declaration ANAF reads as a
        second shipment."""
        picking = self._picking()
        batch = self._batch(picking)
        batch.l10n_ro_edi_stock_state = "stock_sent"
        picking.invalidate_recordset(["l10n_ro_edi_stock_enable"])
        self.assertFalse(picking.l10n_ro_edi_stock_enable)

    def test_a_finished_batch_leaves_nothing_to_notify(self):
        picking = self._picking()
        batch = self._batch(picking)
        batch.state = "done"
        picking.invalidate_recordset(["l10n_ro_edi_stock_enable"])
        self.assertFalse(picking.l10n_ro_edi_stock_enable)

    # ------------------------------------------------------------------
    # Valoarea declarata pentru lot
    # ------------------------------------------------------------------
    def _value(self, batch, op_type):
        move = batch.picking_ids.move_ids[:1]
        return batch._l10n_ro_edi_stock_compute_value(move, op_type)

    def test_goods_going_out_are_worth_their_selling_price(self):
        self.assertEqual(self._value(self._batch(), "20"), 100.0)

    def test_goods_coming_in_are_worth_their_cost(self):
        batch = self._batch(self._picking(self.incoming_type))
        self.assertEqual(self._value(batch, "10"), 40.0)

    def test_the_batch_decides_the_price_source_for_all_its_transfers(self):
        """One lorry, one rule: the batch's choice wins over whatever each
        transfer would have picked on its own."""
        batch = self._batch(l10n_ro_edi_stock_price_source="cost")
        self.assertEqual(self._value(batch, "20"), 40.0)

    def test_the_list_price_can_be_asked_for(self):
        batch = self._batch(
            self._picking(self.incoming_type), l10n_ro_edi_stock_price_source="list"
        )
        self.assertEqual(self._value(batch, "10"), 100.0)

    def test_a_national_delivery_is_worth_its_selling_price(self):
        self.assertEqual(self._value(self._batch(), "30"), 100.0)

    # ------------------------------------------------------------------
    # Adresele celor doua capete
    # ------------------------------------------------------------------
    def test_on_a_delivery_we_are_the_start_and_the_customer_the_end(self):
        batch = self._batch()
        warehouse = batch.picking_type_id.warehouse_id.partner_id
        self.assertEqual(
            batch._l10n_ro_edi_stock_resolve_address_partner("start", "20"), warehouse
        )
        self.assertEqual(
            batch._l10n_ro_edi_stock_resolve_address_partner("end", "20"), self.partner
        )

    def test_on_a_receipt_the_two_ends_swap(self):
        batch = self._batch(self._picking(self.incoming_type))
        warehouse = batch.picking_type_id.warehouse_id.partner_id
        self.assertEqual(
            batch._l10n_ro_edi_stock_resolve_address_partner("end", "10"), warehouse
        )
        self.assertEqual(
            batch._l10n_ro_edi_stock_resolve_address_partner("start", "10"),
            self.partner,
        )

    # ------------------------------------------------------------------
    # Ce imprumuta lotul de la transfer
    # ------------------------------------------------------------------
    def test_the_quantity_and_unit_are_read_the_same_way_as_on_a_transfer(self):
        batch = self._batch()
        move = batch.picking_ids.move_ids[:1]
        self.assertEqual(
            batch._l10n_ro_edi_stock_get_qty_and_uom(move),
            batch.picking_ids[:1]._l10n_ro_edi_stock_get_qty_and_uom(move),
        )

    def test_the_weights_are_read_the_same_way_as_on_a_transfer(self):
        batch = self._batch()
        move = batch.picking_ids.move_ids[:1]
        picking = batch.picking_ids[:1]
        self.assertEqual(
            batch._l10n_ro_edi_stock_compute_net_weight(move),
            picking._l10n_ro_edi_stock_compute_net_weight(move),
        )
        self.assertEqual(
            batch._l10n_ro_edi_stock_compute_gross_weight(move),
            picking._l10n_ro_edi_stock_compute_gross_weight(move),
        )

    def test_the_tariff_code_is_read_the_same_way_as_on_a_transfer(self):
        batch = self._batch()
        self.assertEqual(
            batch._l10n_ro_edi_stock_get_codtarifar(self.product),
            batch.picking_ids[:1]._l10n_ro_edi_stock_get_codtarifar(self.product),
        )

    # ------------------------------------------------------------------
    # Configurarea
    # ------------------------------------------------------------------
    def test_a_new_batch_takes_the_price_source_of_the_company(self):
        self.company.l10n_ro_edi_stock_default_price_source = "cost"
        self.assertEqual(
            self.env["stock.picking.batch"]._l10n_ro_edi_stock_default_price_source(),
            "cost",
        )

    def test_without_a_company_setting_the_source_is_decided_per_operation(self):
        self.company.l10n_ro_edi_stock_default_price_source = False
        self.assertEqual(
            self.env["stock.picking.batch"]._l10n_ro_edi_stock_default_price_source(),
            "auto",
        )

    def test_the_post_outage_flag_is_off_until_somebody_sets_it(self):
        """OUG 41/2022: declaring late is allowed only after an ANAF outage,
        and somebody has to say so."""
        self.assertFalse(self._batch().l10n_ro_edi_stock_post_outage)
