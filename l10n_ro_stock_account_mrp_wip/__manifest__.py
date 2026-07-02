# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

{
    "name": "Romania - MRP Account WIP",
    "category": "Localization",
    "summary": "Romania - MRP Account WIP",
    "depends": ["l10n_ro_stock_account", "mrp_account"],
    "version": "19.0.1.0.0",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "contact@nexterp.ro",
    "images": ["static/description/icon.png"],
    "data": [
        "views/account_move_views.xml",
        "views/mrp_bom_views.xml",
        "views/mrp_production_views.xml",
        "views/product_views.xml",
        "views/product_category_views.xml",
        "wizard/res_config_settings_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "license": "LGPL-3",
}
