# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Inter Company Account",
    "summary": """
        This module helps to identify if an account move line
        and account move is inter company transaction or not.""",
    "version": "16.0.1.0.0",
    "category": "Accounting",
    "depends": ["nexterp_inter_company", "account"],
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "data": [
        # views
        "views/account_move_line_views.xml",
        "views/account_move_views.xml",
        "report/account_move_report_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "images": ["static/description/apps_icon.png"],
    "license": "OPL-1",
}
