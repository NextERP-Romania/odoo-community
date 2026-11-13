# Copyright 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""The <locatie> address written in the eTransport XML.

ANAF rejects an empty attribute (its Str* types have minLength 1), so a blank
address field must leave the attribute out. It must not break the rendering
either: the base template reads data_*_loc['alteInfo'] and the other keys
with square brackets, so they have to stay in the data, set to None.
"""

from unittest.mock import patch

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_ro_edi_stock.models.etransport_api import ETransportAPI


@tagged("post_install", "-at_install")
class TestEtransportAddress(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ro = cls.env.ref("base.ro")

        def state(code):
            return cls.env["res.country.state"].search(
                [("country_id", "=", ro.id), ("code", "=", code)], limit=1
            )

        cls.company = cls.env.company
        cls.company.write(
            {
                "country_id": ro.id,
                "state_id": state("B").id,
                "city": "Bucuresti",
                "street": "Strada Academiei 10",
                "zip": "010011",
                "vat": "RO12345674",
                "account_fiscal_country_id": ro.id,
            }
        )
        cls.customer = cls.env["res.partner"].create(
            {
                "name": "Client",
                "is_company": True,
                "country_id": ro.id,
                "state_id": state("CJ").id,
                "city": "Cluj-Napoca",
                "street": "Strada Memorandumului 28",
                "zip": "400114",
                "vat": "RO76543210",
            }
        )
        transporter = cls.env["res.partner"].create(
            {
                "name": "Transportator",
                "country_id": ro.id,
                "city": "Iasi",
                "street": "Bulevardul Stefan cel Mare 5",
                "vat": "RO24681350",
            }
        )
        carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Curier",
                "product_id": cls.env["product.product"]
                .create({"name": "Livrare", "type": "service"})
                .id,
                "l10n_ro_edi_stock_partner_id": transporter.id,
            }
        )
        product = cls.env["product.product"].create(
            {
                "name": "Marfa",
                "type": "consu",
                "weight": 2.5,
                "standard_price": 100.0,
                "list_price": 150.0,
            }
        )
        out_type = cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", cls.company.id)], limit=1
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.customer.id,
                "carrier_id": carrier.id,
                "picking_type_id": out_type.id,
                "location_id": out_type.default_location_src_id.id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "move_ids": [(0, 0, {"product_id": product.id, "product_uom_qty": 2})],
            }
        )
        cls.picking.action_confirm()
        cls.picking.l10n_ro_edi_stock_operation_type = "30"
        scopes = cls.picking.l10n_ro_edi_stock_available_operation_scopes
        cls.picking.write(
            {
                "l10n_ro_edi_stock_operation_scope": scopes.split(",")[0].strip(),
                "l10n_ro_edi_stock_start_loc_type": "location",
                "l10n_ro_edi_stock_end_loc_type": "location",
                "l10n_ro_edi_stock_vehicle_number": "CJ01ABC",
            }
        )

    def _send_and_capture(self):
        """Run the real send, but stop at the HTTP call to ANAF and return
        the XML that would have been uploaded. The data checks are skipped
        (no access token in tests): only the rendering is under test."""
        captured = {}

        def fake_upload(api, company_id, data):
            captured["xml"] = str(data)
            return {"error": "not sent: test"}

        Picking = type(self.env["stock.picking"])
        with (
            patch.object(ETransportAPI, "upload_data", fake_upload),
            patch.object(
                Picking, "_l10n_ro_edi_stock_validate_data", lambda self, data: []
            ),
        ):
            self.picking._l10n_ro_edi_stock_send_etransport_document("send")
        self.assertIn("xml", captured, "The XML was not rendered")
        return captured["xml"]

    def _locatie(self, loc_key):
        xml = self._send_and_capture()
        root = etree.fromstring(xml.encode())
        (locatie,) = root.xpath(
            f"//*[local-name()='{loc_key}']/*[local-name()='locatie']"
        )
        return locatie.attrib

    def _destination(self):
        return self._locatie("locFinalTraseuRutier")

    # ------------------------------------------------------------------
    # Street2 -> alteInfo
    # ------------------------------------------------------------------
    def test_an_unset_street2_leaves_alteinfo_out(self):
        self.customer.street2 = False
        self.assertNotIn("alteInfo", self._destination())

    def test_an_empty_street2_leaves_alteinfo_out(self):
        """An empty string (from an import or an API) used to crash the
        rendering with KeyError: 'alteInfo'."""
        self.customer.street2 = ""
        self.assertNotIn("alteInfo", self._destination())

    def test_a_street2_of_only_spaces_leaves_alteinfo_out(self):
        self.customer.street2 = "   "
        self.assertNotIn("alteInfo", self._destination())

    def test_a_one_character_street2_is_kept(self):
        """ANAF accepts one character (minLength 1)."""
        self.customer.street2 = "A"
        self.assertEqual(self._destination()["alteInfo"], "A")

    def test_a_filled_street2_is_written_as_alteinfo(self):
        self.customer.street2 = "Bloc 3, Ap. 12"
        self.assertEqual(self._destination()["alteInfo"], "Bloc 3, Ap. 12")

    def test_the_start_address_drops_an_empty_street2_too(self):
        self.company.partner_id.street2 = ""
        self.assertNotIn("alteInfo", self._locatie("locStartTraseuRutier"))

    # ------------------------------------------------------------------
    # Other address fields
    # ------------------------------------------------------------------
    def test_an_empty_zip_leaves_codpostal_out(self):
        self.customer.zip = ""
        self.assertNotIn("codPostal", self._destination())

    def test_the_filled_address_fields_are_all_written(self):
        attrs = self._destination()
        self.assertEqual(attrs["denumireLocalitate"], "Cluj-Napoca")
        self.assertEqual(attrs["denumireStrada"], "Strada Memorandumului")
        self.assertEqual(attrs["numar"], "28")
        self.assertEqual(attrs["codPostal"], "400114")
        self.assertTrue(attrs["codJudet"])

    def test_no_attribute_is_ever_written_empty(self):
        self.customer.write({"street2": "", "zip": " "})
        for name, value in self._destination().items():
            self.assertTrue(value.strip(), f"{name} is empty")
