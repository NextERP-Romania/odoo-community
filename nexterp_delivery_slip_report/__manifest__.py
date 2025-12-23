# Copyright 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Stock Delivery Slip Report",
    "version": "16.0.1.0.2",
    "summary": """ NextERP - Stock Delivery Slip Report""",
    "category": "Warehouse",
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "license": "OPL-1",
    "currency": "EUR",
    "data": [
        "views/report_picking.xml",
        "views/uom_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "depends": ["stock"],
    "installable": True,
    "auto_install": False,
    "application": False,
}
