# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Allow Debt Recovery Invoice",
    "summary": """NextERP - Allow Debt Recovery Invoice""",
    "version": "17.0.1.0.0",
    "category": "Invoicing",
    "depends": ["account"],
    "data": [
        # views
        "views/account_move_view.xml",
        "views/res_config_settings_views.xml",
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
