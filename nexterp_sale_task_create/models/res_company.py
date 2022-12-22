# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_create_taks_auto = fields.Boolean(string="Auto Create Sale Tasks")
