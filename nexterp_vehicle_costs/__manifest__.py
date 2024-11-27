# Copyright (C) 2016 Forest AND Biomass Romania SA
# Copyright (C) 2024 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Vehicle Cost Management",
    "version": "17.0.1.0.0",
    "category": "Managing vehicles and contracts",
    "depends": ["fleet", "account_fleet", "l10n_ro_nondeductible_vat", "stock"],
    "summary": "Manage vehicle costs, add categories for fuel and part, etc.",
    "data": [
        "security/ir.model.access.csv",
        "data/fleet_service_type_data.xml",
        "views/fleet_view.xml",
        "views/stock_view.xml",
        "views/invoice_view.xml",
        "views/fleet_board_view.xml",
    ],
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "odooapps@nexterp.ro",
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "license": "AGPL-3",
}
