# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Sale Order Line Duplicate",
    "summary": "Sale Order Line Duplicate",
    "version": "18.0.1.0.0",
    "category": "Sale",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "depends": [
        "sale",
    ],
    "data": [
        "views/sale_view.xml",
        "wizard/sale_line_duplicate_view.xml",
        "security/ir.model.access.csv",
    ],
    "application": False,
    "installable": True,
    "maintainers": ["feketemihai"],
    "license": "AGPL-3",
}
