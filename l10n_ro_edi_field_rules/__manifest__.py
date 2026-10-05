# Copyright 2026 NextERP Romania
# License LGPL-3
{
    "author": "NextERP Romania",
    "name": "Romania - E-invoicing Field Rules per Partner",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "summary": "Fill CIUS-RO XML nodes differently for each partner",
    "website": "https://www.nexterp.ro",
    "depends": [
        "l10n_ro_edi_extension",
    ],
    "data": [
        "security/l10n_ro_edi_field_rules_groups.xml",
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
