from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_ro_edi_extension.models.utils import _safe_xml_fromstring


@tagged("post_install", "-at_install")
class TestSpvXmlParser(TransactionCase):
    def test_external_entities_are_not_resolved(self):
        root = _safe_xml_fromstring(
            b'<!DOCTYPE root [<!ENTITY marker "expanded">]><root>&marker;</root>'
        )
        self.assertIsNone(root.text)
        self.assertEqual(root[0].name, "marker")

    def test_malformed_schema_location_is_still_supported(self):
        root = _safe_xml_fromstring(
            b'<root xmlns:schemaLocation="http://www.w3.org/2001/XMLSchema '
            b'http://example.test/schema.xsd"/>'
        )
        self.assertEqual(
            root.get("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"),
            "http://www.w3.org/2001/XMLSchema http://example.test/schema.xsd",
        )
