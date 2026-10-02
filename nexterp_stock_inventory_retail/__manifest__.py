# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Stock Inventory Retail",
    "summary": "Markup and deferred VAT on the inventory report",
    "version": "20.0.1.0.0",
    "license": "AGPL-3",
    "images": ["static/description/apps_icon.png"],
    "category": "Generic Modules/Stock",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "depends": [
        "nexterp_stock_inventory",
        "l10n_ro_stock_account_retail",
    ],
    "data": [
        "views/stock_inventory_view.xml",
        "report/stock_inventory_report.xml",
    ],
    "installable": True,
    "auto_install": True,
    "maintainers": ["feketemihai"],
}
