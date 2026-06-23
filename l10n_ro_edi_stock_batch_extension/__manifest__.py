# Copyright 2026 NextERP Romania SRL
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
{
    "name": "Romania - eTransport Batch Extension",
    "summary": "Brings the l10n_ro_edi_stock_extension facilities to batch transfers",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "license": "LGPL-3",
    "images": ["static/description/apps_icon.png"],
    "depends": [
        "l10n_ro_edi_stock_batch",
        "l10n_ro_edi_stock_extension",
    ],
    "data": [
        "wizards/l10n_ro_edi_stock_action_wizard_views.xml",
        "views/stock_picking_batch_views.xml",
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
