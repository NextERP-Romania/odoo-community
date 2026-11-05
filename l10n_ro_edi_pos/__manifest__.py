{
    "author": "NextERP Romania",
    "name": "Romania - E-invoicing Invoices Issued for a Fiscal Receipt",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations/EDI",
    "summary": "An invoice issued for a sale already on a fiscal receipt goes "
    "to ANAF with type code 751",
    "website": "https://www.nexterp.ro",
    "depends": [
        "point_of_sale",
        "l10n_ro_edi",
    ],
    "data": [
        "views/pos_order_views.xml",
        "views/account_move_views.xml",
    ],
    "license": "LGPL-3",
    "images": ["static/description/apps_icon.png"],
    "installable": True,
    "auto_install": False,
}
