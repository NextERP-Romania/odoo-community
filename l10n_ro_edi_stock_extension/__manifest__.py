# Copyright 2026 NextERP Romania SRL
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
{
    "name": "Romania - eTransport Extension",
    "summary": "Fixes and extensions for l10n_ro_edi_stock per ANAF eTransport v2.0.2",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "license": "LGPL-3",
    "depends": [
        "l10n_ro_edi_stock",
        "purchase_stock",
        "sale_stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/etransport_templates.xml",
        "data/ir_cron.xml",
        "wizards/l10n_ro_edi_stock_action_wizard_views.xml",
        "wizards/l10n_ro_edi_stock_list_wizard_views.xml",
        "wizards/l10n_ro_edi_stock_transporter_info_wizard_views.xml",
        "views/res_config_settings_views.xml",
        "views/stock_picking_views.xml",
        "views/l10n_ro_edi_stock_previous_notification_views.xml",
        "views/l10n_ro_edi_stock_document_views.xml",
    ],
    "auto_install": True,
    "installable": True,
    "application": False,
}
