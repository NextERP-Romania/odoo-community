# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Purchase Exception",
    "summary": "Custom exceptions on purchase order line",
    "version": "17.0.1.0.0",
    "category": "Generic Modules/Purchase",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "depends": ["purchase_exception"],
    "license": "AGPL-3",
    "data": [
        "views/purchase_view.xml",
    ],
    "installable": True,
    "maintainers": ["feketemihai"],
    "development_status": "Mature",
}
