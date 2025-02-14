# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class L10nROCPVCode(models.Model):
    _name = "l10n.ro.cpv.code"

    name = fields.Char("Name")
    code = fields.Char("Code")
