# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Base CSV Export",
    "summary": "Base implementation for CSV Export",
    "version": "18.0.1.0.0",
    "category": "Base",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
    ],
    "application": False,
    "installable": True,
    "maintainers": ["feketemihai"],
    "license": "AGPL-3",
}
