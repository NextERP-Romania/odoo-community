{
    "name": "BOM Excel Import",
    "version": "18.0.1.0.0",
    "category": "Manufacturing",
    "summary": """
        This module allows importing Bills of Materials (BOMs) from Excel files.

        The Excel file should have the following structure:
        - Column 1: Product produced
        - Column 2: List of operations in the BOM
        - Column 3: Quantity consumed in each operation
        - Column 4: Product/component consumed UOM
        - Column 5: Product/component consumed
        - Column 6: Workcenter

        The import process uses multi step wizard:
        1. Import operations and workcenters
        2. Import BOMs with the operations

        The wizard guides you through the complete process in a single interface.
    """,
    "author": "NextERP Romania",
    "website": "https://github.com/NextERP-Romania/odoo-community",
    "license": "OPL-1",
    "depends": [
        "mrp",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/bom_excel_import_wizard.xml",
        "views/menu.xml",
    ],
    "external_dependencies": {
        "python": ["openpyxl"],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
