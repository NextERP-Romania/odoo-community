# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).

{
    "name": "Romania - POS Cash Register",
    "summary": "The sessions of a point of sale as a list at the till, and "
    "the cash register of each one printed from there or from the back "
    "office, on the Romanian register form",
    "version": "20.0.1.1.0",
    "license": "AGPL-3",
    "images": ["static/description/apps_icon.png"],
    "category": "Localization/Point of Sale",
    "countries": ["ro"],
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "depends": [
        "pos_actions",
        "point_of_sale",
        "l10n_ro_account_bank_statement_report",
    ],
    "data": [
        "views/pos_session_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "l10n_ro_pos_cash_register/static/src/**/*",
        ],
    },
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["feketemihai"],
}
