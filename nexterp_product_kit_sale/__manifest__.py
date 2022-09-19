# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Product Kit Sale",
    "version": "15.0.1.0.1",
    "depends": ["nexterp_product_kit", "sale"],
    "description": """Product Kits Sale""",
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "contact@nexterp.ro",
    "data": [
        # views
        "views/sale_order_views.xml",
        # security
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "license": "OPL-1",
}
