# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later
{
    "name": "NextERP - Conformity Certificate",
    "summary": "NextERP - Conformity Certificate",
    "version": "20.0.1.0.0",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "category": "Special",
    "depends": ["sale_stock", "l10n_ro_stock_picking_comment_template"],
    "data": ["report/certificat_conformitate.xml"],
    "auto_install": False,
    # Not installable on 20.0: depends on
    # l10n_ro_stock_picking_comment_template, itself held back by
    # base_comment_template (OCA), which has no Odoo 20 counterpart yet.
    # Flip back once it is available.
    "installable": False,
    "license": "AGPL-3",
    "images": ["static/description/apps_icon.png"],
}
