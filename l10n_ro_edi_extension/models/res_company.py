# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_ro_edi_residence = fields.Integer(string="Period of Residence", default=5)
    l10n_ro_edi_error_notify_users = fields.Many2many(
        "res.users",
        relation="res_company_res_users_edi_notify_rel",
        string="EDI Error Notify Users",
        help="Add users to receive EDI Error messages",
    )

    @api.constrains("l10n_ro_edi_residence")
    def _check_l10n_ro_edi_residence(self):
        for company in self:
            if company.l10n_ro_edi_residence < 0 or company.l10n_ro_edi_residence > 5:
                raise models.ValidationError(
                    self.env._("The period of residence must be between 0 and 5.")
                )
