# Copyright (C) 2016 Forest AND Biomass Romania SA
# Copyright (C) 2021 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Vehicle Cost Management",
    "version": "15.0.1.0.0",
    "category": "Managing vehicles and contracts",
    "depends": ["fleet", "l10n_ro_nondeductible_vat"],
    "data": [
        "security/ir.model.access.csv",
        "views/fleet_view.xml",
        "views/stock_view.xml",
        "views/invoice_view.xml",
        "views/product_view.xml",
    ],
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "support": "odooapps@nexterp.ro",
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "license": "AGPL-3",
}
