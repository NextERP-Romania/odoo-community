# Copyright 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Stock Delivery Slip Report",
    "version": "0.0.0",
    "summary": """ NextERP - Stock Delivery Slip Report""",
    "category": "Warehouse",
    "author": "NextERP Romania",
    "website": "https://github.com/NextERP-Romania/odoo-community",
    "support": "odoo_apps@nexterp.ro",
    "license": "OPL-1",
    "currency": "EUR",
    "data": [
        "views/report_picking.xml",
        "views/res_config_settings_views.xml",
    ],
    "depends": ["stock", "nexterp_account_invoice_report"],
    "installable": True,
    "auto_install": False,
    "application": False,
}
