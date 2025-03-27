# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Romania - Edi CPV",
    "summary": "Romania - Edi CPV",
    "version": "16.0.1.0.0",
    "category": "Localisation",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "depends": ["l10n_ro_account_edi_ubl", "account_edi_ubl_cii"],
    "data": [
        "data/cpv_code.xml",
        "views/res_partner.xml",
        "views/product.xml",
        "views/ubl_templates.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "license": "AGPL-3",
}
