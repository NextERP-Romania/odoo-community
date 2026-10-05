# Copyright 2026 NextERP Romania
# License LGPL-3
"""The catalog is only useful if every path it offers can actually be rendered."""

from odoo.tests import TransactionCase, tagged

from odoo.addons.account_edi_ubl_cii.tools.ubl_21_credit_note import (
    CreditNote,
    CreditNoteLine,
)
from odoo.addons.account_edi_ubl_cii.tools.ubl_21_invoice import Invoice, InvoiceLine

from ..tools.ciusro_fields import CIUSRO_FIELDS

TEMPLATES = {
    "document": {
        "invoice": ("Invoice", Invoice),
        "credit_note": ("CreditNote", CreditNote),
    },
    "line": {
        "invoice": ("InvoiceLine", InvoiceLine),
        "credit_note": ("CreditNoteLine", CreditNoteLine),
    },
}


@tagged("post_install", "-at_install")
class TestCiusRoFields(TransactionCase):
    def test_every_path_exists_in_the_ubl_templates(self):
        """dict_to_xml raises on a tag missing from the template, so a wrong
        path in the catalog would break the export at send time."""
        for key, entry in CIUSRO_FIELDS.items():
            doc_types = entry.get("doc_types", ("invoice", "credit_note"))
            for doc_type, (template_name, template) in TEMPLATES[
                entry["scope"]
            ].items():
                if doc_type not in doc_types:
                    continue
                node = template
                for tag in entry["path"]:
                    self.assertIsInstance(
                        node,
                        dict,
                        f"{key}: '{tag}' has no children in {template_name}",
                    )
                    self.assertIn(
                        tag,
                        node,
                        f"{key}: '{tag}' is not part of {template_name}",
                    )
                    node = node[tag]

    def test_keys_are_unique_per_node(self):
        """Two entries may share a path only when they write different parts
        of the node (its text and one of its attributes)."""
        seen = {}
        for key, entry in CIUSRO_FIELDS.items():
            target = (entry["scope"], entry["path"], entry.get("attribute"))
            self.assertNotIn(target, seen, f"{key} duplicates {seen.get(target)}")
            seen[target] = key
