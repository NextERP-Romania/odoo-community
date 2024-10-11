# Copyright 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).
{
    "name": "Base CSV Export",
    "summary": "Base implementation for CSV Export",
    "version": "16.0.0.0.1",
    "category": "Base",
    "author": "NextERP Romania",
    "website": "https://nexterp.ro",
    "license": "OPL-1",
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
    ],
}
