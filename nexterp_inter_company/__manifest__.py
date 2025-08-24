# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/18.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Inter Company",
    "summary": """
        This module helps to identify if a record is inter
        company transaction or not.""",
    "version": "18.0.0.0.0",
    "category": "Base",
    "depends": ["base"],
    "author": "NextERP Romania",
    "website": "https://github.com/NextERP-Romania/odoo-community",
    "support": "odoo_apps@nexterp.ro",
    "data": ["views/res_partner.xml"],
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "images": ["static/description/apps_icon.png"],
    "license": "OPL-1",
}
