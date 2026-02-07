# Copyright (C) 2025 NextERP Romania
# License LGPL-3 or later

{
    "name": "NextERP - Account EDI Journalt",
    "version": "19.0.0.0.0",
    "summary": """ NextERP - Account EDI Journal""",
    "category": "Accounting",
    "author": "NextERP Romania",
    "website": "https://github.com/NextERP-Romania/odoo-community",
    "support": "odoo_apps@nexterp.ro",
    "license": "LGPL-3",
    "currency": "EUR",
    "data": [
        "views/account_journal_views.xml",
    ],
    "depends": ["l10n_ro_account_edi_ubl"],
    "installable": True,
    "auto_install": False,
    "application": False,
}
