# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Sale Update Prices Auto",
    "version": "15.0.1.0.1",
    "depends": ["sale_management"],
    "description": """NextERP - Sale Update Prices Auto""",
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "contact@nexterp.ro",
    "data": [
        # views
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "license": "OPL-1",
}
