# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Stock Picking Sequence",
    "summary": "Transfers get their number when they are validated, not when "
    "they are created, so the numbering has no gaps",
    "version": "19.0.1.0.1",
    "category": "Stock",
    "depends": ["stock"],
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
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
