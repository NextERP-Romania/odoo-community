# Copyright 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Analytic Distribution Models by Journal",
    "version": "17.0.1.0.0",
    "summary": """Match analytic distribution models by journal.""",
    "category": "Accounting/Analytic",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "license": "OPL-1",
    "currency": "EUR",
    "depends": ["account"],
    "data": [
        "views/account_analytic_distribution_model_views.xml",
    ],
    "development_status": "Mature",
    "installable": True,
    "auto_install": False,
    "application": False,
    "maintainers": ["feketemihai"],
}
