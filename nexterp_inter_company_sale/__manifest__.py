# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Inter Company Sale",
    "summary": """This module helps to identify if an sale order line """
    """and sale order is inter company transaction or not.""",
    "version": "16.0.1.0.0",
    "category": "Sales",
    "depends": ["nexterp_inter_company", "sale"],
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "data": [
        # views
        "views/sale_order_views.xml",
        "report/sale_report_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "images": ["static/description/apps_icon.png"],
    "license": "OPL-1",
}
