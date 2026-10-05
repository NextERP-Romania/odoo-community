# Copyright 2026 NextERP Romania
# License LGPL-3
"""The rules must reach the generated XML, and the right rule must win."""

from lxml import etree

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.l10n_ro_edi.tests.common import TestROEdiCommon


@tagged("post_install_l10n", "post_install", "-at_install")
class TestXmlFieldRules(TestROEdiCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Maintaining the mapping is a group of its own, and expressions and
        # raw XML paths are reserved to the technical users on top of it.
        cls.env.user.group_ids += cls.env.ref(
            "l10n_ro_edi_configurable_tags.group_l10n_ro_edi_xml_rule_manager"
        ) | cls.env.ref("base.group_system")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "default_code": "OUR-REF-1",
            }
        )
        cls.profile = cls.env["l10n_ro.edi.xml.profile"].create(
            {
                "name": "Retail GS1",
            }
        )
        cls.partner_ro.l10n_ro_edi_profile_id = cls.profile

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _rule(self, **vals):
        vals.setdefault("profile_id", self.profile.id)
        return self.env["l10n_ro.edi.xml.rule"].create(vals)

    def _export(self, invoice=None):
        invoice = invoice or self.create_invoice(
            invoice_line_ids=[
                Command.create(
                    {
                        "product_id": self.product.id,
                        "quantity": 1,
                        "price_unit": 500.0,
                        "tax_ids": [Command.set(self.tax_19.ids)],
                    }
                ),
            ],
        )
        xml, errors = self.env["account.edi.xml.ubl_ro"]._export_invoice(invoice)
        return etree.fromstring(xml), errors

    def _text(self, tree, path):
        node = tree.find(path)
        return node.text if node is not None else None

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_fixed_value_reaches_the_xml(self):
        self._rule(
            field_key="buyer_reference",
            value_type="fixed",
            value_fixed="4001",
        )
        tree, errors = self._export()
        self.assertFalse(errors)
        self.assertEqual(self._text(tree, "{*}BuyerReference"), "4001")

    def test_field_value_reaches_the_xml(self):
        self._rule(
            field_key="line_buyers_item_id",
            value_type="field",
            field_path="product_id.default_code",
        )
        tree, _errors = self._export()
        self.assertEqual(
            self._text(
                tree,
                "{*}InvoiceLine/{*}Item/{*}BuyersItemIdentification/{*}ID",
            ),
            "OUR-REF-1",
        )

    def test_rule_overwrites_what_odoo_computed(self):
        """Odoo falls back to the invoice name for the purchase order
        reference; a retailer needs its own number there."""
        self._rule(
            field_key="order_reference",
            value_type="fixed",
            value_fixed="PO-123456",
        )
        tree, _errors = self._export()
        self.assertEqual(self._text(tree, "{*}OrderReference/{*}ID"), "PO-123456")

    def test_rule_without_overwrite_keeps_odoo_value(self):
        self._rule(
            field_key="order_reference",
            value_type="fixed",
            value_fixed="PO-123456",
            overwrite=False,
        )
        tree, _errors = self._export()
        self.assertNotEqual(self._text(tree, "{*}OrderReference/{*}ID"), "PO-123456")

    def test_partner_rule_beats_profile_rule(self):
        self._rule(
            field_key="buyer_reference",
            value_type="fixed",
            value_fixed="from profile",
        )
        self._rule(
            profile_id=False,
            partner_id=self.partner_ro.id,
            field_key="buyer_reference",
            value_type="fixed",
            value_fixed="from partner",
        )
        tree, _errors = self._export()
        self.assertEqual(self._text(tree, "{*}BuyerReference"), "from partner")

    def test_value_is_truncated_to_the_schematron_limit(self):
        self._rule(
            field_key="accounting_cost",
            value_type="fixed",
            value_fixed="X" * 150,
        )
        tree, _errors = self._export()
        self.assertEqual(len(self._text(tree, "{*}AccountingCost")), 100)

    def test_remove_drops_the_node(self):
        self._rule(field_key="order_reference", value_type="remove")
        tree, _errors = self._export()
        self.assertIsNone(self._text(tree, "{*}OrderReference/{*}ID"))

    def test_rule_limited_to_credit_notes_is_skipped_on_invoices(self):
        self._rule(
            field_key="buyer_reference",
            value_type="fixed",
            value_fixed="4001",
            document_types="credit_note",
        )
        tree, _errors = self._export()
        self.assertIsNone(self._text(tree, "{*}BuyerReference"))

    def test_required_rule_without_value_blocks_the_export(self):
        self._rule(
            field_key="buyer_reference",
            value_type="field",
            field_path="invoice_origin",
            value_required=True,
        )
        invoice = self.create_invoice(invoice_origin=False)
        _tree, errors = self._export(invoice)
        self.assertTrue(errors)

    def test_attribute_rules_write_an_attribute(self):
        self._rule(
            field_key="line_standard_item_id",
            value_type="fixed",
            value_fixed="5901234123457",
        )
        self._rule(
            field_key="line_standard_item_scheme",
            value_type="fixed",
            value_fixed="0160",
        )
        tree, _errors = self._export()
        node = tree.find("{*}InvoiceLine/{*}Item/{*}StandardItemIdentification/{*}ID")
        self.assertEqual(node.text, "5901234123457")
        self.assertEqual(node.get("schemeID"), "0160")

    def test_unknown_path_is_refused(self):
        with self.assertRaises(ValidationError):
            self._rule(
                field_key="custom",
                scope="document",
                xml_path="cac:NotAUblNode/cbc:ID",
                value_type="fixed",
                value_fixed="x",
            )

    def test_node_missing_on_credit_notes_is_refused_for_both(self):
        """ProjectReference only exists on an Invoice; the catalog narrows the
        rule down on its own, and widening it back is refused."""
        rule = self._rule(
            field_key="project_reference",
            value_type="fixed",
            value_fixed="PRJ-1",
        )
        self.assertEqual(rule.document_types, "invoice")
        with self.assertRaises(ValidationError):
            rule.document_types = "all"

    def test_expression_needs_the_technical_group(self):
        accountant = self.env["res.users"].create(
            {
                "name": "Accountant",
                "login": "ro_edi_rules_accountant",
                "group_ids": [
                    Command.set(
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref(
                                "l10n_ro_edi_configurable_tags."
                                "group_l10n_ro_edi_xml_rule_manager"
                            ).id,
                        ]
                    )
                ],
            }
        )
        with self.assertRaises(ValidationError):
            self.env["l10n_ro.edi.xml.rule"].with_user(accountant).create(
                {
                    "profile_id": self.profile.id,
                    "field_key": "buyer_reference",
                    "value_type": "expression",
                    "expression": "move.name",
                }
            )

    def test_json_round_trip(self):
        self._rule(
            field_key="buyer_reference",
            value_type="fixed",
            value_fixed="4001",
        )
        target = self.env["l10n_ro.edi.xml.profile"].create({"name": "Copy"})
        self.env["l10n_ro.edi.xml.profile.import"].create(
            {
                "profile_id": target.id,
                "json_text": self.profile.json_export,
                "mode": "replace",
            }
        ).action_import()
        self.assertEqual(len(target.rule_ids), 1)
        self.assertEqual(target.rule_ids.value_fixed, "4001")
