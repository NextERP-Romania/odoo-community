# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - cron deactivation notify",
    "summary": """NextERP - cron deactivation notify""",
    "version": "16.0.0.0.1",
    "category": "Action",
    "depends": [
        "base",
        "mail",
    ],
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "license": "OPL-1",
    "data": [
        # views
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "images": ["static/description/apps_icon.png"],
}
