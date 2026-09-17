# Copyright 2026 NextERP Romania SRL
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
{
    "name": "Romania - eTransport Batch Extension",
    "summary": "Brings the l10n_ro_edi_stock_extension facilities to batch transfers",
    "version": "20.0.1.2.0",
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
        "views/l10n_ro_edi_stock_document_views.xml",
    ],
    "auto_install": True,
    # Not installable on 20.0: depends on l10n_ro_edi_stock_batch (scos din Odoo in 20.0), which has no Odoo 20
    # counterpart yet. Flip back once it is available.
    "installable": False,
    "application": False,
}
