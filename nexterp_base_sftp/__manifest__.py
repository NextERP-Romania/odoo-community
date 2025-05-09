# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "SFTP Server",
    "summary": "Base implementation for SFTP Server",
    "version": "18.0.1.0.0",
    "category": "Localisation",
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "views/sftp_server_view.xml",
        "security/sftp_server_security.xml",
        "security/ir.model.access.csv",
    ],
    "external_dependencies": {
        "python": [
            "paramiko",
        ]
    },
    "application": False,
    "installable": True,
    "maintainers": ["feketemihai"],
    "license": "AGPL-3",
}
