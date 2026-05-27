{
    "author": "NextERP Romania",
    "name": "Romania - E-invoicing Extension",
    "version": "19.0.1.0.1",
    "category": "Accounting/Localizations/EDI",
    "summary": "E-Invoice implementation for Romania",
    "website": "https://www.nexterp.ro",
    "depends": [
        "l10n_ro_edi",
        "l10n_ro_message_spv",
    ],
    "data": [
        "data/account_edi_cron_data.xml",
        "views/account_move_views.xml",
        "wizard/res_config_settings_views.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": True,
}
