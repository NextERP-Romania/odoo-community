# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


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

    def _cron_l10n_ro_edi_synchronize_invoices(self):
        """
        The standard synchronization cron only handles companies with an
        OAuth client (client_id, client_secret, refresh token). Also run it
        for companies that have an access token but no client_id, logging any
        UserError per company the way the standard cron does.
        """
        res = super()._cron_l10n_ro_edi_synchronize_invoices()

        ro_companies = (
            self.env["res.company"]
            .sudo()
            .search(
                [
                    ("l10n_ro_edi_access_token", "!=", False),
                    ("l10n_ro_edi_client_id", "=", False),
                ]
            )
        )
        for company in ro_companies:
            try:
                self.env["account.move"].with_company(
                    company
                )._l10n_ro_edi_fetch_invoices()
            except UserError as e:
                self._l10n_ro_edi_log_message(
                    message=f"{company.id}\n{e}",
                    func="_cron_l10n_ro_edi_synchronize_invoices",
                )
        return res
