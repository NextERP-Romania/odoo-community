# Copyright 2026 NextERP Romania
# License LGPL-3
{
    "author": "NextERP Romania",
    "name": "Romania - E-invoicing Configurable Tags",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "summary": "Configure per partner which CIUS-RO XML tags are filled, and with what",
    "website": "https://www.nexterp.ro",
    "depends": [
        "l10n_ro_edi_extension",
    ],
    "data": [
        "security/l10n_ro_edi_configurable_tags_groups.xml",
        "security/ir.model.access.csv",
        "views/l10n_ro_edi_xml_rule_views.xml",
        "views/l10n_ro_edi_xml_profile_views.xml",
        "wizard/l10n_ro_edi_xml_profile_import_views.xml",
        "views/res_partner_views.xml",
        "views/menus.xml",
    ],
    "license": "LGPL-3",
    "images": ["static/description/apps_icon.png"],
    "installable": True,
}
