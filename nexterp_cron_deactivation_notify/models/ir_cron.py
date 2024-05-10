# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import models


class ir_cron(models.Model):
    _inherit = "ir.cron"

    def write(self, vals):
        if vals.get('active') is False and not self.env.context.get('module'):
            for cron in self:
                ir_config_database_param = self.env["ir.config_parameter"].sudo().get_param("database.is_neutralized")
                if not ir_config_database_param or ir_config_database_param == 'False':
                    config_settings = self.env['res.config.settings'].search([])
                    users_to_notify = config_settings.mapped('archived_cron_notify_users_ids')
                    if users_to_notify:
                        mail_subject = "Notification: Archived Cron Job"
                        mail_body = f"The following cron job have been archived: \n {cron.name} \n"
                        mail_values = {
                                'subject': mail_subject,
                                'body_html': mail_body,
                                'recipient_ids': users_to_notify.mapped('partner_id').ids,
                                'notification': True,
                            }
                        self.env['mail.mail'].sudo().create(mail_values).send()
        return super().write(vals)
