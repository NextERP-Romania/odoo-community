# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Purchase Exception",
    "summary": "Custom exceptions on purchase order line",
    "version": "19.0.0.0.0",
    "category": "Generic Modules/Purchase",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "depends": ["purchase_exception"],
    "license": "AGPL-3",
    "images": ["static/description/apps_icon.png"],
    "data": [
        "views/purchase_view.xml",
    ],
    "installable": True,
    "maintainers": ["feketemihai"],
    "development_status": "Mature",
}
