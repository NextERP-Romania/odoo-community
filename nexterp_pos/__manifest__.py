# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).

{
    "name": "NextERP POS",
    "summary": "Keep several sessions open on one register and close them oldest first",
    "version": "20.0.3.0.0",
    "license": "AGPL-3",
    "images": ["static/description/apps_icon.png"],
    "category": "Generic Modules/Point of Sale",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "depends": [
        "point_of_sale",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "maintainers": ["feketemihai"],
}
