# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Product Kit Sale",
    "summary": "NextERP - Product Kit Sale",
    "version": "17.0.1.0.0",
    "category": "Sales",
    "depends": ["nexterp_product_kit", "sale"],
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "data": [
        # views
        "views/sale_order_views.xml",
        # security
        "security/ir.model.access.csv",
    ],
    "installable": False,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "images": ["static/description/apps_icon.png"],
    "license": "OPL-1",
}
