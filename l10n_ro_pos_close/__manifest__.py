# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).

{
    "name": "Romania - POS Closing Differences",
    "summary": "Record the differences per payment method at the closing of a "
    "POS session and print the report that explains them",
    "version": "20.0.1.0.0",
    "license": "AGPL-3",
    "category": "Localization/Point of Sale",
    "countries": ["ro"],
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "depends": [
        "point_of_sale",
        "l10n_ro",
    ],
    "data": [
        "security/ir.access.csv",
        "views/pos_closing_line_views.xml",
        "views/pos_session_views.xml",
        "wizard/pos_closing_note_views.xml",
        "report/pos_session_closing_report.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "l10n_ro_pos_close/static/src/**/*",
        ],
    },
    "installable": True,
    "development_status": "Beta",
    "maintainers": ["feketemihai"],
}
