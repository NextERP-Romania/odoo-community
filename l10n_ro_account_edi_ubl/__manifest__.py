# Copyright (C) 2022 Dorin Hongu <dhongu(@)gmail(.)com
# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Romania - eFactura Account EDI UBL",
    "summary": "Romania - eFactura - Account EDI UBL",
    "version": "18.0.1.0.0",
    "category": "Localization",
    "author": "Terrabit," "NextERP Romania," "Odoo Community Association (OCA)",
    "website": "https://www.nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "depends": [
        "l10n_ro_config",
        "l10n_ro_edi",
        "l10n_ro_partner_create_by_vat",
    ],
    "data": [
        "data/account_edi_data.xml",
        "views/res_config_settings_views.xml",
        "views/account_invoice.xml",
        "views/cius_template.xml",
        "views/product_view.xml",
        "views/res_partner.xml",
    ],
    "installable": True,
    "development_status": "Mature",
    "maintainers": ["dhongu", "feketemihai"],
    "license": "AGPL-3",
}
