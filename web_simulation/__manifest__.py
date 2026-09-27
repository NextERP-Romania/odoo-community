# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Web Simulation",
    "summary": "Run a document's buttons without saving, and see what they "
    "would do to stock and to the books",
    "version": "20.0.1.0.0",
    "license": "LGPL-3",
    "category": "Tools",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    # stock_account brings stock and account: the result points at products,
    # locations and accounts. The other models it looks for (purchase, sale,
    # POS, MRP) are resolved at runtime, so they stay optional.
    "depends": ["web", "stock_account"],
    "data": [
        "security/res_groups.xml",
        "security/ir.access.csv",
        "wizard/simulation_run_views.xml",
        "wizard/simulation_edit_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "web_simulation/static/src/**/*.js",
            "web_simulation/static/src/**/*.xml",
        ],
    },
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["feketemihai"],
}
