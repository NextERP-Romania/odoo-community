# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Analytic Default Rules by Journal",
    "summary": """NextERP - Analytic Default Rules by Journal""",
    "version": "14.0.1.0.1",
    "category": "Invoicing",
    "depends": ["account"],
    "data": [
        "views/account_analytic_default_views.xml",
    ],
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "images": ["static/description/apps_icon.png"],
    "license": "OPL-1",
}
