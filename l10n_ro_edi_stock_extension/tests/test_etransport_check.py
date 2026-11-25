# Copyright 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Checking a transfer before it is sent, and before it is validated.

What used to come back from ANAF as a schema error is found here first and
told to the user in words, one line per product.
"""

import base64
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestEtransportCheck(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.l10n_ro_edi_access_token = "token"
        cls.partner = cls.env["res.partner"].create(
            {"name": "Client DE", "country_id": cls.env.ref("base.de").id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Spuma", "is_storable": True, "list_price": 10.0, "weight": 0.0}
        )
        cls.out_type = cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", cls.company.id)], limit=1
        )

    def _picking(self, **vals):
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.out_type.id,
                "location_id": self.out_type.default_location_src_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "scheduled_date": fields.Datetime.now(),
                "l10n_ro_edi_stock_operation_type": "20",
                "l10n_ro_edi_stock_operation_scope": "101",
                "l10n_ro_edi_stock_vehicle_number": "BN01ABC",
                "move_ids": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 2})
                ],
                **vals,
            }
        )
        picking.action_confirm()
        return picking

    def test_a_product_without_data_gets_one_readable_line(self):
        picking = self._picking()
        errors = picking._l10n_ro_edi_stock_check_errors()
        lines = [e for e in errors if e.startswith("Product ")]
        self.assertEqual(len(lines), 1)
        self.assertIn("no tariff (NC8) code", lines[0])
        self.assertIn("no weight", lines[0])

    def test_the_base_intrastat_message_is_not_repeated(self):
        picking = self._picking()
        errors = picking._l10n_ro_edi_stock_check_errors()
        self.assertFalse([e for e in errors if "intrastat code value" in e])

    def test_checking_sends_and_stores_nothing(self):
        picking = self._picking()
        picking._l10n_ro_edi_stock_check_errors()
        self.assertFalse(picking.l10n_ro_edi_stock_document_ids)

    def test_the_check_button_lists_the_errors(self):
        picking = self._picking()
        with self.assertRaisesRegex(UserError, "cannot be sent to eTransport yet"):
            picking.action_l10n_ro_edi_stock_check()

    def test_a_new_notification_is_declared_for_today(self):
        """The UIT is valid from 00:00 of dataTransport; declaring today
        lets the vehicle be changed or the transport confirmed right away,
        whatever the scheduled date."""
        picking = self._picking(
            scheduled_date=fields.Datetime.now() + timedelta(days=2)
        )
        data = {"_picking_record": picking, "send_type": "send"}
        picking._l10n_ro_edi_stock_set_transport_date(data)
        self.assertEqual(
            data["scheduled_date"].date(), fields.Date.context_today(picking)
        )
        errors = picking._l10n_ro_edi_stock_check_errors()
        self.assertFalse([e for e in errors if "outside the interval" in e])

    def test_a_chosen_transport_date_is_sent(self):
        picking = self._picking()
        chosen = fields.Date.context_today(picking) + timedelta(days=2)
        picking.l10n_ro_edi_stock_transport_date = chosen
        data = {"_picking_record": picking, "send_type": "send"}
        picking._l10n_ro_edi_stock_set_transport_date(data)
        self.assertEqual(data["scheduled_date"].date(), chosen)

    def test_the_transport_start_defaults_to_today(self):
        picking = self._picking()
        self.assertEqual(
            picking.l10n_ro_edi_stock_transport_date,
            fields.Date.context_today(picking),
        )

    def test_the_transport_start_is_limited_to_today_plus_three(self):
        picking = self._picking()
        today = fields.Date.context_today(picking)
        picking.l10n_ro_edi_stock_transport_date = today + timedelta(days=3)
        for days in (-1, 4):
            with self.assertRaises(ValidationError):
                picking.l10n_ro_edi_stock_transport_date = today + timedelta(days=days)

    def test_a_past_scheduled_date_does_not_stop_the_notification(self):
        picking = self._picking(
            scheduled_date=fields.Datetime.now() - timedelta(days=30)
        )
        errors = picking._l10n_ro_edi_stock_check_errors()
        self.assertFalse([e for e in errors if "outside the interval" in e])

    def test_a_post_outage_declaration_may_start_in_the_past(self):
        picking = self._picking(l10n_ro_edi_stock_post_outage=True)
        past = fields.Date.context_today(picking) - timedelta(days=1)
        picking.l10n_ro_edi_stock_transport_date = past
        data = {"_picking_record": picking, "send_type": "send"}
        picking._l10n_ro_edi_stock_set_transport_date(data)
        self.assertEqual(data["scheduled_date"].date(), past)

    def test_a_correction_keeps_the_declared_date(self):
        picking = self._picking()
        declared = fields.Date.context_today(picking) - timedelta(days=1)
        xml = f'<dateTransport dataTransport="{declared}"/>'
        self.env["l10n_ro_edi.document"].create(
            {
                "picking_id": picking.id,
                "state": "stock_validated",
                "l10n_ro_edi_stock_uit": "UIT1",
                "attachment": base64.b64encode(xml.encode()),
            }
        )
        self.assertEqual(picking._l10n_ro_edi_stock_declared_transport_date(), declared)
        picking.l10n_ro_edi_stock_operation_type = "20"
        self.assertEqual(picking.l10n_ro_edi_stock_uit_valid_from, declared)
        self.assertEqual(
            picking.l10n_ro_edi_stock_uit_valid_until, declared + timedelta(days=4)
        )
        for op_type in ("10", "12", "14", "60"):
            picking.l10n_ro_edi_stock_operation_type = op_type
            self.assertEqual(
                picking.l10n_ro_edi_stock_uit_valid_until,
                declared + timedelta(days=14),
            )
        picking.l10n_ro_edi_stock_operation_type = "40"
        self.assertEqual(
            picking.l10n_ro_edi_stock_uit_valid_until, declared + timedelta(days=4)
        )
        data = {"_picking_record": picking, "send_type": "amend"}
        picking._l10n_ro_edi_stock_set_transport_date(data)
        self.assertEqual(data["scheduled_date"].date(), declared)

    def test_validation_is_stopped_when_the_data_is_incomplete(self):
        picking = self._picking()
        picking.move_ids.quantity = 2
        picking.l10n_ro_edi_stock_enable = True
        with self.assertRaisesRegex(
            UserError, "missing a delivery carrier|eTransport data is incomplete"
        ):
            picking.button_validate()

    def test_validation_is_free_without_an_operation_type(self):
        picking = self._picking(l10n_ro_edi_stock_operation_type=False)
        self.assertFalse(picking._l10n_ro_edi_stock_pickings_to_check_on_validate())

    def test_a_token_problem_is_transient_an_anaf_refusal_is_not(self):
        mixin = self.env["stock.picking"]
        self.assertTrue(
            mixin._l10n_ro_edi_stock_is_transient_error("Access token is forbidden.")
        )
        self.assertFalse(mixin._l10n_ro_edi_stock_is_transient_error("UIT inactiv."))
