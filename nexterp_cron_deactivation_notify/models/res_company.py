# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    archived_cron_notify_users_ids = fields.Many2many(
        "res.users",
        "res_company_archived_cron_notify_users_ids_rel",
    )
