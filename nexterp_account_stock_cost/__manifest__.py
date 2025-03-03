# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Account Stock Cost",
    "summary": """NextERP - Account Stock Cost""",
    "version": "14.0.1.0.0",
    "category": "Invoicing",
    "depends": ["account", "sale_stock", "purchase_stock", "l10n_ro_stock_account","nexterp_analytic_account"],
    "data": ["account_invoice_report.xml","account_move_line.xml"],
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "license": "OPL-1",
}