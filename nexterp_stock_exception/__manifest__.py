# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Stock Exception",
    "summary": "Custom exceptions on stock move",
    "version": "15.0.1.0.0",
    "category": "Generic Modules/Stock",
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "depends": ["stock_exception"],
    "license": "AGPL-3",
    "data": [
        "views/stock_view.xml",
    ],
    "installable": True,
    "maintainers": ["feketemihai"],
}
