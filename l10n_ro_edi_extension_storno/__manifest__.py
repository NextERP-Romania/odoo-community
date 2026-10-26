{
    "author": "NextERP Romania",
    "name": "Romania - E-invoicing Storno Credit Notes",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "summary": "Send customer credit notes to ANAF as invoice 380 with negative values",
    "website": "https://www.nexterp.ro",
    "depends": [
        "l10n_ro_edi_extension",
    ],
    "data": [
        "views/report_invoice.xml",
        "wizard/res_config_settings_views.xml",
    ],
    "license": "LGPL-3",
    "images": ["static/description/apps_icon.png"],
    "installable": True,
    "auto_install": False,
}
