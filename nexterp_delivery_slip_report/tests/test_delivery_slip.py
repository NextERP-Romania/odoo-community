# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""What the printed delivery note says and in which language.

Three choices a company makes once: whether the internal reference is
printed next to the product name, how many decimals a unit is printed with,
and whether incoming notes are printed in the company's language instead of
the supplier's.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDeliverySlipReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.partner_id.lang = "en_US"
        cls.env["res.lang"]._activate_lang("ro_RO")
        cls.partner = cls.env["res.partner"].create({"name": "Client", "lang": "ro_RO"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Marfa",
                "default_code": "COD-1",
                "is_storable": True,
            }
        )

    def _picking(self, code="outgoing"):
        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", code), ("company_id", "=", self.company.id)], limit=1
        )
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
                            "product_uom_qty": 3,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        # The printed lines come from the detailed operations, which only
        # exist once the transfer has something to move.
        self.env["stock.quant"]._update_available_quantity(
            self.product, picking.location_id, 3
        )
        picking.action_assign()
        return picking

    def _printed_names(self, picking):
        aggregated = picking.move_line_ids._get_aggregated_product_quantities()
        return [line["name"] for line in aggregated.values()]

    # ------------------------------------------------------------------
    # Numele produsului
    # ------------------------------------------------------------------
    def test_by_default_the_internal_reference_is_printed_too(self):
        picking = self._picking()
        self.assertTrue(any("COD-1" in name for name in self._printed_names(picking)))

    def test_with_the_setting_on_only_the_name_is_printed(self):
        """The customer has no use for our own code."""
        self.company.delivery_slip_report_only_name = True
        picking = self._picking()
        self.assertEqual(self._printed_names(picking), ["Marfa"])

    def test_every_printed_line_carries_the_precision_of_its_unit(self):
        self.product.uom_id.report_precision = 3
        picking = self._picking()
        aggregated = picking.move_line_ids._get_aggregated_product_quantities()
        self.assertEqual(
            [line["report_precision"] for line in aggregated.values()], [3]
        )

    # ------------------------------------------------------------------
    # Limba documentului
    # ------------------------------------------------------------------
    def test_a_delivery_note_is_printed_in_the_customer_language(self):
        self.assertEqual(self._picking()._get_report_lang(), "ro_RO")

    def test_an_incoming_note_follows_the_supplier_until_told_otherwise(self):
        self.assertEqual(self._picking("incoming")._get_report_lang(), "ro_RO")

    def test_with_the_setting_on_incoming_notes_use_our_own_language(self):
        """A goods receipt is read here, not by the supplier."""
        self.company.picking_report_lang_company = True
        self.assertEqual(self._picking("incoming")._get_report_lang(), "en_US")

    def test_the_setting_does_not_touch_what_the_customer_receives(self):
        self.company.picking_report_lang_company = True
        self.assertEqual(self._picking()._get_report_lang(), "ro_RO")

    def test_the_settings_follow_the_company(self):
        for field in (
            "delivery_slip_report_only_name",
            "delivery_slip_report_uom_precision",
            "picking_report_lang_company",
        ):
            self.assertFalse(self.env["res.config.settings"].create({})[field], field)
            self.company[field] = True
            self.assertTrue(self.env["res.config.settings"].create({})[field], field)
