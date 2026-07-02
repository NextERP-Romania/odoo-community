# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import fields, models


class MrpBom(models.Model):
    _name = "mrp.bom"
    _inherit = ["mrp.bom", "l10n.ro.mixin"]

    l10n_ro_auto_wip_accounting = fields.Boolean(
        string="Auto WIP Accounting",
        help="If checked, the WIP accounts will be automatically handled "
        "during manufacturing operations.",
    )
