# Copyright (C) 2024 NextERP Romania SRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "NextERP - Account UBL Extra Code",
    "summary": """NextERP - Adds additional codes to e-factura such as delivery slip number,
    customer item code,GLN code and EAN cod""",
    "version": "14.0.1.0.2",
    "category": "Invoicing",
    "depends": ["account", "l10n_ro_account_edi_ubl"],
    "data": ["views/ubl_template.xml"],
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "images": ["static/description/apps_icon.png"],
    "license": "AGPL-3",
}
