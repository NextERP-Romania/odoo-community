from odoo import api, models


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _get_default_sending_methods(self, move) -> set:
        if self.env.context.get("l10n_ro_send_to_anaf"):
            return {}
        return super()._get_default_sending_methods(move)

    @api.model
    def _hook_invoice_document_before_pdf_report_render(self, invoice, invoice_data):
        res = super()._hook_invoice_document_before_pdf_report_render(
            invoice, invoice_data
        )
        if "ro_edi" in invoice_data["extra_edis"] and invoice_data.get("error"):
            if invoice.company_id.l10n_ro_edi_error_notify_users:
                for user in invoice.company_id.l10n_ro_edi_error_notify_users:
                    invoice.activity_schedule(
                        activity_type_id=self.env.ref(
                            "mail.mail_activity_data_warning"
                        ).id,
                        summary=self.env._("Error while sending the invoice to SPV"),
                        note=self.env._(
                            "The invoice could not be sent to the ANAF SPV. "
                            "Please check the error and resend it once fixed."
                        ),
                        user_id=user.id,
                    )
        return res
