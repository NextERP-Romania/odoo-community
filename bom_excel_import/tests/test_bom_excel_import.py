# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Bringing a whole bill of materials in from a spreadsheet.

The file is read twice: the first pass opens the work centres, the bills and
their operations, the second pass fills the bills with components. Products
that are not in Odoo yet are created along the way, so a factory can start
from the list it already keeps in Excel.
"""

import io

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import BinaryBytes

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None


def _workbook(rows, sheet_name="Sheet1"):
    """An .xlsx with a header row and `rows` under it, as bytes."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(
        [
            "Produs",
            "Operatie",
            "Cantitate",
            "UM",
            "Componenta",
            "Centru de lucru",
            "Subcontractare",
            "Subcontractanti",
        ]
    )
    for row in rows:
        sheet.append(list(row))
    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


@tagged("post_install", "-at_install")
class TestBomExcelImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if openpyxl is None:  # pragma: no cover
            cls.skipTest(cls, "openpyxl is not installed")
        cls.Wizard = cls.env["bom.excel.import.wizard"]

    def _wizard(self, rows, **vals):
        return self.Wizard.create(
            {
                "excel_file": BinaryBytes(_workbook(rows)),
                "filename": "bom.xlsx",
                **vals,
            }
        )

    def _import(self, rows, **vals):
        wizard = self._wizard(rows, **vals)
        wizard.action_start_import()
        wizard.action_import_operations()
        wizard.action_import_boms()
        return wizard

    def _bom_of(self, product_name):
        product = self.env["product.product"].search(
            [("name", "=", product_name)], limit=1
        )
        return self.env["mrp.bom"].search([("product_id", "=", product.id)], limit=1)

    # ------------------------------------------------------------------
    # Fisierul
    # ------------------------------------------------------------------
    def test_a_file_that_is_not_a_spreadsheet_is_refused(self):
        wizard = self.Wizard.create(
            {"excel_file": BinaryBytes(b"nu e xlsx"), "filename": "bom.xlsx"}
        )
        with self.assertRaises(UserError):
            wizard.action_start_import()

    def test_a_sheet_that_is_not_in_the_file_is_named_in_the_message(self):
        wizard = self._wizard([("Masa", "Taiere", 4, "Units", "Picior", "Atelier")])
        wizard.sheet_name = "Lipsa"
        with self.assertRaises(UserError) as caught:
            wizard.action_start_import()
        self.assertIn("Sheet1", str(caught.exception))

    def test_a_good_file_moves_the_wizard_to_the_next_step(self):
        wizard = self._wizard([("Masa", "Taiere", 4, "Units", "Picior", "Atelier")])
        wizard.action_start_import()
        self.assertEqual(wizard.step, "operations")

    # ------------------------------------------------------------------
    # Pasul intai: centre de lucru, retete, operatii
    # ------------------------------------------------------------------
    def test_the_import_opens_a_bom_for_the_product(self):
        self._import([("Masa", "Taiere", 4, "Units", "Picior", "Atelier")])
        self.assertTrue(self._bom_of("Masa"))

    def test_a_product_that_is_not_in_odoo_is_created(self):
        self._import([("Masa", "Taiere", 4, "Units", "Picior", "Atelier")])
        for name in ("Masa", "Picior"):
            product = self.env["product.product"].search([("name", "=", name)])
            self.assertEqual(len(product), 1, name)
            self.assertTrue(product.is_storable)

    def test_a_product_that_is_already_there_is_reused(self):
        """The spreadsheet must not fill the catalogue with duplicates."""
        existing = self.env["product.product"].create(
            {"name": "Masa", "is_storable": True}
        )
        self._import([("Masa", "Taiere", 4, "Units", "Picior", "Atelier")])
        self.assertEqual(
            self.env["product.product"].search_count([("name", "=", "Masa")]), 1
        )
        self.assertEqual(self._bom_of("Masa").product_id, existing)

    def test_the_work_centre_named_in_the_file_is_opened(self):
        wizard = self._import([("Masa", "Taiere", 4, "Units", "Picior", "Atelier")])
        self.assertEqual(wizard.workcenters_created, 1)
        self.assertTrue(self.env["mrp.workcenter"].search([("name", "=", "Atelier")]))

    def test_a_work_centre_that_already_exists_is_reused(self):
        self.env["mrp.workcenter"].create({"name": "Atelier"})
        wizard = self._import([("Masa", "Taiere", 4, "Units", "Picior", "Atelier")])
        self.assertEqual(wizard.workcenters_created, 0)
        self.assertEqual(
            self.env["mrp.workcenter"].search_count([("name", "=", "Atelier")]), 1
        )

    def test_the_operations_land_on_the_bom_in_the_order_they_are_listed(self):
        self._import(
            [
                ("Masa", "Taiere", 4, "Units", "Picior", "Atelier"),
                ("Masa", "Asamblare", 1, "Units", "Blat", "Atelier"),
            ]
        )
        operations = self._bom_of("Masa").operation_ids.sorted("sequence")
        self.assertEqual(operations.mapped("name"), ["Taiere", "Asamblare"])

    def test_the_same_operation_named_twice_is_created_once(self):
        self._import(
            [
                ("Masa", "Taiere", 4, "Units", "Picior", "Atelier"),
                ("Masa", "Taiere", 1, "Units", "Blat", "Atelier"),
            ]
        )
        self.assertEqual(len(self._bom_of("Masa").operation_ids), 1)

    def test_a_row_without_a_product_is_skipped(self):
        wizard = self._import(
            [
                (None, "Taiere", 4, "Units", "Picior", "Atelier"),
                ("Masa", "Taiere", 4, "Units", "Picior", "Atelier"),
            ]
        )
        self.assertEqual(wizard.boms_created, 1)

    def test_two_products_get_two_boms(self):
        wizard = self._import(
            [
                ("Masa", "Taiere", 4, "Units", "Picior", "Atelier"),
                ("Scaun", "Taiere", 1, "Units", "Sezut", "Atelier"),
            ]
        )
        self.assertEqual(wizard.boms_created, 2)

    # ------------------------------------------------------------------
    # Pasul al doilea: componentele
    # ------------------------------------------------------------------
    def test_the_components_land_on_the_bom_with_their_quantities(self):
        self._import(
            [
                ("Masa", "Taiere", 4, "Units", "Picior", "Atelier"),
                ("Masa", "Asamblare", 1, "Units", "Blat", "Atelier"),
            ]
        )
        lines = self._bom_of("Masa").bom_line_ids
        self.assertEqual(
            dict(
                zip(
                    lines.product_id.mapped("name"),
                    lines.mapped("product_qty"),
                    strict=False,
                )
            ),
            {"Picior": 4.0, "Blat": 1.0},
        )

    def test_a_quantity_that_is_not_a_number_falls_back_to_one(self):
        self._import([("Masa", "Taiere", "patru", "Units", "Picior", "Atelier")])
        self.assertEqual(self._bom_of("Masa").bom_line_ids.product_qty, 1.0)

    def test_a_row_without_a_component_adds_no_line(self):
        self._import([("Masa", "Taiere", 4, "Units", None, "Atelier")])
        self.assertFalse(self._bom_of("Masa").bom_line_ids)

    def test_the_wizard_ends_on_the_last_step_with_a_log(self):
        wizard = self._import([("Masa", "Taiere", 4, "Units", "Picior", "Atelier")])
        self.assertEqual(wizard.step, "complete")
        self.assertTrue(wizard.operations_completed)
        self.assertTrue(wizard.bom_completed)
        self.assertIn("Masa", wizard.operations_import_log)
        self.assertIn("Picior", wizard.bom_import_log)
        self.assertEqual(wizard.bom_lines_created, 1)

    def test_starting_over_clears_what_the_last_run_left(self):
        wizard = self._import([("Masa", "Taiere", 4, "Units", "Picior", "Atelier")])
        wizard.action_restart()
        self.assertEqual(wizard.step, "upload")
        self.assertFalse(wizard.operations_import_log)
        self.assertFalse(wizard.bom_completed)
        self.assertEqual(wizard.boms_created, 0)

    def test_the_header_row_is_not_imported(self):
        """The first row names the columns; `start_row` is what skips it."""
        wizard = self._import([("Masa", "Taiere", 4, "Units", "Picior", "Atelier")])
        self.assertEqual(wizard.boms_created, 1)
        self.assertFalse(self.env["product.product"].search([("name", "=", "Produs")]))
