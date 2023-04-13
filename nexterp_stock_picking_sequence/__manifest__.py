# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Stock Picking Sequence",
    "summary": """NextERP - Stock Picking Sequence""",
    "version": "15.0.1.0.2",
    "category": "Stock",
    "depends": ["stock"],
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "data": [
        # views
        "views/res_config_settings_views.xml",
        "data/data.xml",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "images": ["static/description/apps_icon.png"],
    "license": "OPL-1",
}
