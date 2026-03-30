import base64
import logging

import requests
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain

from .utils import (
    _request_ciusro_synchronize_invoices,
    _request_ciusro_xml_to_pdf,
)

_logger = logging.getLogger(__name__)

HOLDING_DAYS = 3  # Arbitrary


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _l10n_ro_edi_fetch_invoices(self):
        """Synchronize bills/invoices from SPV"""
        nb_days = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_ro_edi_nb_days_to_fetch", default=1)
        )
        _logger.info(
            "Starting synchronization of sent invoices with SPV for the last %s days",
            nb_days,
        )
        result = _request_ciusro_synchronize_invoices(
            company=self.env.company,
            session=requests.Session(),
            nb_days=int(nb_days),
        )
        if result.get("errors"):
            raise UserError(result["errors"])

        if result["sent_invoices_accepted_messages"]:
            self._l10n_ro_edi_process_invoice_accepted_messages(
                result["sent_invoices_accepted_messages"]
            )

        if result["sent_invoices_refused_messages"]:
            self._l10n_ro_edi_process_invoice_refused_messages(
                result["sent_invoices_refused_messages"]
            )

        if result["received_bills_messages"]:
            self._l10n_ro_edi_process_bill_messages(result["received_bills_messages"])

        # Non-indexed moves that were not processed after some time have probably been refused by the SPV. Since
        # there is no way to recover the index for refused invoices, we simply refuse them manually without proper reason.
        domain = (
            Domain("company_id", "=", self.env.company.id)
            & Domain("l10n_ro_edi_index", "=", False)
            & Domain("l10n_ro_edi_state", "=", "invoice_not_indexed")
        )
        non_indexed_invoices = self.env["account.move"].search(domain)

        document_ids_to_delete = []
        for invoice in non_indexed_invoices:
            # At that point, only one sent document should exists on an invoice
            sent_document = invoice.l10n_ro_edi_document_ids

            if (
                fields.Datetime.today() - sent_document.create_date
            ).days > HOLDING_DAYS:
                document_ids_to_delete += invoice.l10n_ro_edi_document_ids.ids

                error_message = _(
                    "The invoice has probably been refused by the SPV. We were unable to recover the reason of the refusal because "
                    "the invoice had not received its index. Duplicate the invoice and attempt to send it again."
                )
                invoice.message_post(body=error_message)
                self.env["l10n_ro_edi.document"].sudo().create(
                    {
                        "invoice_id": invoice.id,
                        "state": "invoice_refused",
                        "message": error_message,
                    }
                )

        self.env["l10n_ro_edi.document"].sudo().browse(document_ids_to_delete).unlink()

        if self._can_commit():
            self.env.cr.commit()

    @api.model
    def _l10n_ro_edi_process_bill_messages(self, received_bills_messages):
        """Create bill received on the SPV, it it does not already exists."""
        # Search potential similar bills: similar bills either:
        # - have an index that is present in the message data or,
        # - the same amount and seller VAT, and optionally the same bill date
        domain = (
            Domain("company_id", "=", self.env.company.id)
            & Domain("move_type", "in", self.get_purchase_types())
            & (
                (
                    Domain("l10n_ro_edi_index", "=", False)
                    & Domain("l10n_ro_edi_state", "=", False)
                    & Domain.OR(
                        [
                            Domain(
                                "amount_total",
                                "=",
                                message["answer"]["invoice"]["amount_total"],
                            )
                            & Domain(
                                "commercial_partner_id.vat",
                                "=",
                                message["answer"]["invoice"]["seller_vat"],
                            )
                            & Domain(
                                "invoice_date",
                                "in",
                                [message["answer"]["invoice"]["date"], False],
                            )
                            for message in received_bills_messages
                            if "error" not in message["answer"]
                        ]
                    )
                )
                | (
                    Domain(
                        "l10n_ro_edi_index",
                        "in",
                        [
                            message["id_solicitare"]
                            for message in received_bills_messages
                        ],
                    )
                    & Domain("l10n_ro_edi_state", "=", "invoice_validated")
                )
            )
        )
        similar_bills = self.env["account.move"].search(domain)

        indexed_similar_bills = similar_bills.filtered("l10n_ro_edi_index").mapped(
            "l10n_ro_edi_index"
        )
        non_indexed_similar_bills_dict = {
            (bill.commercial_partner_id.vat, bill.amount_total, bill.invoice_date): bill
            for bill in similar_bills
            if not bill.l10n_ro_edi_index
        }

        for message in received_bills_messages:
            if "error" in message["answer"]:
                continue

            if message["id_solicitare"] in indexed_similar_bills:
                # A bill with the same SPV index was already imported, skip it as we don't want it twice.
                continue

            # Create new bills if they don't already exist, else update their content
            bill = non_indexed_similar_bills_dict.get(
                (
                    message["answer"]["invoice"]["seller_vat"],
                    float(message["answer"]["invoice"]["amount_total"]),
                    message["answer"]["invoice"]["date"],
                )
            )
            if not bill:
                bill = non_indexed_similar_bills_dict.get(
                    (
                        message["answer"]["invoice"]["seller_vat"],
                        float(message["answer"]["invoice"]["amount_total"]),
                        False,
                    )
                )
            if not bill:
                bill = self.env["account.move"].create(
                    {
                        "company_id": self.env.company.id,
                        "move_type": "in_invoice",
                        "journal_id": self.env.company.l10n_ro_edi_anaf_imported_inv_journal_id.id,
                    }
                )

            bill.l10n_ro_edi_index = message["id_solicitare"]

            self.env["l10n_ro_edi.document"].sudo().create(
                {
                    "invoice_id": bill.id,
                    "state": "invoice_validated",
                    "key_download": message["id"],
                    "key_signature": message["answer"]["signature"]["key_signature"],
                    "key_certificate": message["answer"]["signature"][
                        "key_certificate"
                    ],
                    "attachment": base64.b64encode(
                        message["answer"]["signature"]["attachment_raw"]
                    ),
                }
            )
            xml_attachment_raw = message["answer"]["invoice"]["attachment_raw"]
            xml_attachment_id = (
                self.env["ir.attachment"]
                .sudo()
                .create(
                    {
                        "name": f"ciusro_{message['answer']['invoice']['name'].replace('/', '_')}.xml",
                        "raw": xml_attachment_raw,
                        "res_model": "account.move",
                        "res_id": bill.id,
                    }
                )
                .id
            )
            files_data = self._to_files_data(
                self.env["ir.attachment"].browse(xml_attachment_id)
            )
            bill._extend_with_attachments(files_data)
            chatter_message = self.env._(
                "Synchronized with SPV from message %s", message["id"]
            )
            # The pdf is generated from _import_attachments method from account_edi_ubl_cii
            # with report 'account_edi_ubl_cii.action_report_account_invoices_generated_by_odoo'
            # We try to fetch the PDF from SPV and replace the main attachment with the one
            # from SPV if the SPV PDF retrieval is successful. Otherwise, we keep the PDF
            # generated by Odoo.
            inv_type = "FACT1" if bill.move_type == "in_invoice" else "FCN"
            validate_xml = "DA"
            pdf = _request_ciusro_xml_to_pdf(
                self.env.company, xml_attachment_raw, inv_type, validate_xml
            )
            if "error" in pdf:
                bill.message_post(
                    body=self.env._(
                        "It was not possible to retrieve the PDF from the SPV for the following reason: %s",
                        pdf["error"],
                    )
                )
            else:
                bill.message_main_attachment_id.unlink()
                pdf_attachment_id = (
                    self.env["ir.attachment"]
                    .sudo()
                    .create(
                        {
                            "name": f"ciusro_{message['answer']['invoice']['name'].replace('/', '_')}.pdf",
                            "raw": pdf["content"],
                            "res_model": "account.move",
                            "res_id": bill.id,
                        }
                    )
                    .id
                )
                bill.message_main_attachment_id = pdf_attachment_id
                chatter_message += Markup("<br/>%s") % self.env._(
                    "No PDF found: PDF imported from SPV."
                )
            bill.message_post(body=chatter_message)

    def action_send_and_print_anaf(self):
        self.env["account.move.send"]._check_move_constraints(self)
        return {
            "name": _("Send"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "account.move.send.wizard"
            if len(self) == 1
            else "account.move.send.batch.wizard",
            "target": "new",
            "context": {
                "active_model": "account.move",
                "active_ids": self.ids,
                "l10n_ro_send_to_anaf": True,
            },
        }
