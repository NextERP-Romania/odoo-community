# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

{
    "name": "POS - Desks",
    "summary": "A line of its own above the register for the desks a shop "
    "works at, so each new one is an entry there instead of another button "
    "crowding the register bar",
    "version": "20.0.1.0.0",
    "license": "LGPL-3",
    "images": ["static/description/apps_icon.png"],
    "category": "Point of Sale",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "depends": ["point_of_sale"],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_actions/static/src/**/*",
        ],
    },
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["feketemihai"],
}
