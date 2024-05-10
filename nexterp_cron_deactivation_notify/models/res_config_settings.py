# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    archived_cron_notify_users_ids = fields.Many2many(
        string="Users to Notify",
        related="company_id.archived_cron_notify_users_ids",
        readonly=False,
    )
