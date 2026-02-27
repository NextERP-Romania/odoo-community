# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Stock Inventory",
    "summary": "Stock Inventory",
    "version": "16.0.1.0.0",
    "category": "Generic Modules/Stock",
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "depends": [
        "stock_account",
    ],
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/stock_inventory_line_report_view.xml",
        "views/stock_inventory_view.xml",
    ],
    "installable": True,
    "maintainers": ["feketemihai"],
}
