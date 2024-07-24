# Copyright 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Account Invoice Report",
    "version": "17.0.1.0.0",
    "summary": """ NextERP - Account Invoice Report""",
    "category": "Accounting",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "license": "OPL-1",
    "currency": "EUR",
    "data": [
        "views/report_invoice.xml",
        "views/res_config_settings_views.xml",
    ],
    "depends": ["account"],
    "development_status": "Mature",
    "installable": True,
    "auto_install": False,
    "application": False,
}
