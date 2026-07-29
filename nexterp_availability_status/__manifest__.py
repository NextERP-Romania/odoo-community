# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Availability Status",
    "summary": "Traffic-light availability status shared across Inventory, "
               "Manufacturing, Sales and Purchase",
    "version": "17.0.1.0.0",
    "category": "Generic Modules/Stock",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "depends": [
        "stock",
        "mrp",
        "sale_stock",
        "purchase_stock",
    ],
    "license": "AGPL-3",
    "data": [
        "views/stock_move_views.xml",
        "views/stock_picking_views.xml",
        "views/mrp_production_views.xml",
        "views/sale_order_views.xml",
        "views/purchase_order_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "nexterp_availability_status/static/src/availability_widget/*.js",
            "nexterp_availability_status/static/src/availability_widget/*.xml",
            "nexterp_availability_status/static/src/availability_widget/*.scss",
        ],
    },
    "installable": True,
    "maintainers": ["feketemihai"],
    "development_status": "Beta",
}
