# Copyright 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - POS Session Closing by Date",
    "version": "16.0.1.0.0",
    "summary": """ NextERP - POS Session Closing by Date""",
    "category": "Sales",
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "license": "OPL-1",
    "currency": "EUR",
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "depends": ["point_of_sale"],
    "installable": True,
    "auto_install": False,
    "application": False,
}
