import base64

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import plaintext2html


class StatementCommon(models.AbstractModel):
    _inherit = "statement.common.wizard"

    def generate_pdf(self):
        """Generează un PDF pe baza datelor din context"""
        report_name = "partner_statement.outstanding_statement"
        active_ids = self.env.context.get("active_ids", [])

        if not active_ids:
            raise ValueError("No active partners selected!")
        report = self.env["ir.actions.report"]._get_report_from_name(report_name)
        pdf_content, content_type = report._render_qweb_pdf(report_name, active_ids)

        attachment = self.env["ir.attachment"].create(
            {
                "name": "Outstanding_Statement.pdf",
                "type": "binary",
                "datas": base64.b64encode(pdf_content),
                "res_model": "res.partner",
                "res_id": active_ids[0],
                "mimetype": "application/pdf",
            }
        )

        return attachment

    def get_body(self, date):
        body = f"""Buna ziua!,

            Va trimitem atasat confirmarea de sold la data de  {date} cu rugamintea de a o completa.

            Va rugam sa trimiteti raspunsul d-voastra la adresa de mail: {self.env.company.email}.

            Multumim!

        """
        return body

    def send_email(self):
        """
        Send by email the followup to the customer's followup contacts
        """
        partner = self.env["res.partner"].browse(self._context["active_ids"])
        email = partner.email
        sent_at_least_once = False
        if email and email.strip():
            self = self.with_context(lang=partner.lang or self.env.user.lang)
            attachment_ids = self.generate_pdf()
            body_html = self.get_body(self.date_end)
            author_id = partner.id

            partner.with_context(
                mail_post_autofollow=True,
                mail_notify_author=True,
                lang=partner.lang or self.env.user.lang,
            ).message_post(
                partner_ids=[partner.id],
                author_id=author_id,
                email_from=self.env.company.email,
                body=plaintext2html(body_html),
                subject=_("Confirmari sold"),
                model_description=_("payment reminder"),
                email_layout_xmlid="mail.mail_notification_light",
                attachment_ids=attachment_ids.ids,
                subtype_id=self.env["ir.model.data"]._xmlid_to_res_id("mail.mt_note"),
            )
            sent_at_least_once = True
        if not sent_at_least_once:
            raise UserError(
                _(
                    "You are trying to send an Email, but no follow-up contact has any email address set for customer '%s'",
                    partner.name,
                )
            )
