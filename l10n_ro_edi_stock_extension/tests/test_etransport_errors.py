# Copyright 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""What the user reads when ANAF rejects the file against its schema.

ANAF answers with the raw Xerces text: a line, a column and a cvc-* code. The
user has to be told which record and which field to fix instead.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_ro_edi_stock_extension.models.etransport_errors import (
    EMPTY,
    INVALID,
    MISSING,
    TOO_LONG,
    guess_attribute,
    locate_element,
    parse_xsd_errors,
)

# A notification ANAF rejected: the destination address has alteInfo="".
REJECTED_XML = """<?xml version='1.0' encoding='UTF-8'?>
<eTransport xmlns="mfp:anaf:dgti:eTransport:declaratie:v2" codDeclarant="1">
<notificare codTipOperatiune="10">
<bunuriTransportate codTarifar="82089000" denumireMarfa="Banda 1" cantitate="13.0"/>
<bunuriTransportate codTarifar="8208" denumireMarfa="Banda 2" cantitate="17.0"/>
<partenerComercial codTara="DE" denumire="SITOLA GMBH" cod="DE813404477"/>
<dateTransport nrVehicul="NHP5000" codOrgTransport="25944870"/>
<locStartTraseuRutier codPtf="1"/>
<locFinalTraseuRutier>
<locatie codJudet="6" denumireLocalitate="Sat" denumireStrada="Nr. A" alteInfo=""/>
</locFinalTraseuRutier>
</notificare>
</eTransport>
"""

EMPTY_STREET2 = (
    "Fisierul transmis nu este valid. org.xml.sax.SAXParseException; "
    "lineNumber: 10; columnNumber: 88; cvc-minLength-valid: Value '' with "
    "length = '0' is not facet-valid with respect to minLength '1' for type "
    "'Str200'."
)


@tagged("post_install", "-at_install")
class TestEtransportErrorParsing(TransactionCase):
    def test_an_empty_value_is_read_with_its_position(self):
        (error,) = parse_xsd_errors(EMPTY_STREET2)
        self.assertEqual(error["line"], 10)
        self.assertEqual(error["col"], 88)
        self.assertEqual(error["code"], "cvc-minLength-valid")
        self.assertEqual(error["kind"], EMPTY)
        self.assertEqual(error["value"], "")
        self.assertIsNone(error["attribute"])

    def test_a_missing_attribute_names_attribute_and_element(self):
        (error,) = parse_xsd_errors(
            "org.xml.sax.SAXParseException; lineNumber: 4; columnNumber: 9; "
            "cvc-complex-type.4: Attribute 'codTarifar' must appear on element "
            "'bunuriTransportate'."
        )
        self.assertEqual(error["kind"], MISSING)
        self.assertEqual(error["attribute"], "codTarifar")
        self.assertEqual(error["element"], "bunuriTransportate")

    def test_a_value_too_long_carries_the_limit(self):
        (error,) = parse_xsd_errors(
            "lineNumber: 6; columnNumber: 3; cvc-maxLength-valid: Value 'xxx' "
            "with length = '3' is not facet-valid with respect to maxLength '2' "
            "for type 'Str2'."
        )
        self.assertEqual(error["kind"], TOO_LONG)
        self.assertEqual(error["max_length"], 2)

    def test_several_errors_on_separate_lines_are_kept_apart(self):
        errors = parse_xsd_errors(
            EMPTY_STREET2
            + "\nFisierul transmis nu este valid. org.xml.sax.SAXParseException; "
            "lineNumber: 4; columnNumber: 9; cvc-pattern-valid: Value '12' is not "
            "facet-valid with respect to pattern '[0-9]{4,8}' for type 'CodTarifar'."
        )
        self.assertEqual([e["line"] for e in errors], [10, 4])
        self.assertEqual(errors[1]["kind"], INVALID)
        self.assertNotIn("Fisierul", errors[0]["original"])

    def test_text_that_is_not_a_schema_error_gives_nothing(self):
        self.assertEqual(parse_xsd_errors("Access token is forbidden."), [])

    def test_the_line_points_to_the_element_in_the_sent_xml(self):
        element = locate_element(REJECTED_XML, 10)
        self.assertEqual(element["tag"], "locatie")
        self.assertEqual(element["parent"], "locFinalTraseuRutier")

    def test_repeated_elements_know_their_position(self):
        element = locate_element(REJECTED_XML, 5)
        self.assertEqual(element["tag"], "bunuriTransportate")
        self.assertEqual(element["index"], 1)

    def test_the_attribute_is_the_one_holding_the_rejected_value(self):
        (error,) = parse_xsd_errors(EMPTY_STREET2)
        element = locate_element(REJECTED_XML, 10)
        self.assertEqual(guess_attribute(error, element), "alteInfo")

    def test_unreadable_xml_locates_nothing(self):
        self.assertIsNone(locate_element("<not xml", 1))


@tagged("post_install", "-at_install")
class TestEtransportErrorMessage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.supplier = cls.env["res.partner"].create({"name": "SITOLA GMBH"})
        cls.product = cls.env["product.product"].create({"name": "Banda"})
        cls.incoming_type = cls.env["stock.picking.type"].search(
            [("code", "=", "incoming"), ("company_id", "=", cls.env.company.id)],
            limit=1,
        )
        cls.warehouse_partner = cls.incoming_type.warehouse_id.partner_id
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.supplier.id,
                "picking_type_id": cls.incoming_type.id,
                "location_id": cls.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": cls.incoming_type.default_location_dest_id.id,
                "move_ids": [
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1}),
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 2}),
                ],
            }
        )

    def test_an_empty_street2_points_to_the_destination_partner(self):
        message = self.picking._l10n_ro_edi_stock_explain_xsd_errors(
            EMPTY_STREET2, REJECTED_XML
        )
        first = message.splitlines()[0]
        self.assertIn("Destination address", first)
        self.assertIn(self.warehouse_partner.display_name, first)
        self.assertIn('"Street2" is empty', first)
        # the original text stays for support
        self.assertIn("cvc-minLength-valid", message)

    def test_a_goods_line_points_to_its_product(self):
        message = self.picking._l10n_ro_edi_stock_explain_xsd_errors(
            "lineNumber: 5; columnNumber: 9; cvc-pattern-valid: Value '8208' is "
            "not facet-valid with respect to pattern '[0-9]{8}' for type 'T'.",
            REJECTED_XML,
        )
        self.assertIn("Product Banda (line 2)", message)
        self.assertIn("8208", message)

    def test_the_failed_document_gets_the_readable_message(self):
        self.picking._l10n_ro_edi_stock_create_document_stock_sending_failed(
            {"message": EMPTY_STREET2, "raw_xml": REJECTED_XML}
        )
        document = self.picking.l10n_ro_edi_stock_document_ids[:1]
        self.assertIn("Destination address", document.message)

    def test_other_errors_are_left_as_they_are(self):
        self.picking._l10n_ro_edi_stock_create_document_stock_sending_failed(
            {"message": "Access token is forbidden.", "raw_xml": REJECTED_XML}
        )
        document = self.picking.l10n_ro_edi_stock_document_ids[:1]
        self.assertEqual(document.message, "Access token is forbidden.")
