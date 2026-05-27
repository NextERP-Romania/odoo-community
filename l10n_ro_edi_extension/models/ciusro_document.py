import requests

from odoo import api, models

from .utils import _request_ciusro_synchronize_invoices_pagination


class L10nRoEdiDocument(models.Model):
    _inherit = "l10n_ro_edi.document"

    @api.model
    def _request_ciusro_download_messages_spv(
        self, company, no_days=60, start=None, end=None, page=1, filtru=""
    ):
        message_response = _request_ciusro_synchronize_invoices_pagination(
            company=company,
            session=requests,
            nb_days=int(no_days or 1),
        )
        messages = message_response.get("messages", [])
        return messages

    @api.model
    def _cius_ro_send_invoices_automatically_cron(self):
        companies = self.env["res.company"].search(
            [("l10n_ro_edi_auto_send_invoices", "=", True)]
        )
        for company in companies:
            self._request_ciusro_download_messages_spv(company=company)
