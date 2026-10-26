# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Romania - E-invoicing Self-Invoices",
    "summary": "Take in the self-invoices customers issue in your name from the SPV",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "license": "AGPL-3",
    "images": ["static/description/apps_icon.png"],
    "depends": [
        "l10n_ro_edi_extension",
        "l10n_ro_message_spv",
    ],
    "data": [
        "views/message_spv_views.xml",
    ],
    "installable": True,
}
