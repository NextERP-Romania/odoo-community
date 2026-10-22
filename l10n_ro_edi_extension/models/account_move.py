import base64
import logging
import re
from datetime import timedelta

import requests
from lxml import etree
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
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
        nb_days = self.env.company.l10n_ro_download_einvoices_days or 1
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

        # Self-billed invoices issued by customers in our name are sales, not
        # bills: take them out before the standard processing sees them.
        autoinvoice_messages = []
        for key, received in (
            ("sent_invoices_accepted_messages", False),
            ("received_bills_messages", True),
        ):
            kept = []
            for message in result[key]:
                if self._l10n_ro_edi_is_autoinvoice_message(message, received):
                    autoinvoice_messages.append(message)
                else:
                    kept.append(message)
            result[key] = kept
        if autoinvoice_messages:
            self._l10n_ro_edi_process_autoinvoice_messages(autoinvoice_messages)

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

        # Non-indexed moves that were not processed after some time have probably
        # been refused by the SPV. Since there is no way to recover the index for
        # refused invoices, we simply refuse them manually without proper reason.
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

                error_message = self.env._(
                    "The invoice has probably been refused by the SPV. We were"
                    " unable to recover the reason of the refusal because the"
                    " invoice had not received its index. Duplicate the invoice"
                    " and attempt to send it again."
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
            # Commit per cron iteration so SPV-processed invoices are persisted
            # even if a later batch raises; matches l10n_ro_edi upstream pattern.
            self.env.cr.commit()  # pylint: disable=invalid-commit

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
                # A bill with the same SPV index was already imported, skip it
                # as we don't want it twice.
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
                imported_journal = (
                    self.env.company.l10n_ro_edi_anaf_imported_inv_journal_id
                )
                bill = self.env["account.move"].create(
                    {
                        "company_id": self.env.company.id,
                        "move_type": "in_invoice",
                        "journal_id": imported_journal.id,
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
            invoice_name = message["answer"]["invoice"]["name"].replace("/", "_")
            xml_attachment_id = (
                self.env["ir.attachment"]
                .sudo()
                .create(
                    {
                        "name": f"ciusro_{invoice_name}.xml",
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
            # The pdf is generated from _import_attachments in account_edi_ubl_cii
            # with report
            # 'account_edi_ubl_cii.action_report_account_invoices_generated_by_odoo'.
            # We try to fetch the PDF from SPV and replace the main attachment
            # with the one from SPV if the retrieval is successful. Otherwise,
            # we keep the PDF generated by Odoo.
            inv_type = "FACT1" if bill.move_type == "in_invoice" else "FCN"
            validate_xml = "DA"
            pdf = _request_ciusro_xml_to_pdf(
                self.env.company, xml_attachment_raw, inv_type, validate_xml
            )
            if "error" in pdf:
                bill.message_post(
                    body=self.env._(
                        "It was not possible to retrieve the PDF from the SPV"
                        " for the following reason: %s",
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
                            "name": f"ciusro_{invoice_name}.pdf",
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

    # ------------------------------------------------------------------
    # Self-billed invoices (autofacturi) issued by customers in our name
    # ------------------------------------------------------------------

    @api.model
    def _l10n_ro_edi_clean_vat(self, vat):
        return re.sub(r"^RO", "", (vat or "").replace(" ", "").upper())

    @api.model
    def _l10n_ro_edi_autoinvoice_customer_vat(self, company, xml_bytes, received=True):
        """Return the customer VAT when the XML is an invoice that customer
        issued in the company's name (autofactura), else False.

        The supplier of such a document is the company and the customer is
        somebody else. A document listed as received was uploaded by somebody
        else, so that is enough; one listed as sent may be one of ours, so it
        must also carry the self-billing type code 389."""
        company_vat = self._l10n_ro_edi_clean_vat(company.vat)
        if not company_vat or not xml_bytes:
            return False
        try:
            tree = etree.fromstring(xml_bytes, parser=etree.XMLParser(recover=True))
        except (etree.XMLSyntaxError, ValueError):
            return False
        if tree is None:
            return False

        def party_vats(role):
            vats = []
            for path in ("PartyTaxScheme", "PartyLegalEntity"):
                for node in tree.findall(
                    f"./{{*}}{role}/{{*}}Party/{{*}}{path}/{{*}}CompanyID"
                ):
                    vat = self._l10n_ro_edi_clean_vat(node.text)
                    if vat and vat not in vats:
                        vats.append(vat)
            return vats

        if company_vat not in party_vats("AccountingSupplierParty"):
            return False
        customer_vats = party_vats("AccountingCustomerParty")
        if not customer_vats or company_vat in customer_vats:
            return False
        if not received and tree.findtext("./{*}InvoiceTypeCode") != "389":
            return False
        return customer_vats[0]

    @api.model
    def _l10n_ro_edi_is_autoinvoice_message(self, message, received):
        answer = message.get("answer") or {}
        invoice = answer.get("invoice") or {}
        if "error" in answer or "error" in invoice:
            return False
        return bool(
            self._l10n_ro_edi_autoinvoice_customer_vat(
                self.env.company, invoice.get("attachment_raw"), received
            )
        )

    @api.model
    def _l10n_ro_edi_partner_from_vat(self, company, vat):
        partner_obj = self.env["res.partner"]
        vat = self._l10n_ro_edi_clean_vat(vat)
        if not vat:
            return partner_obj
        for variant in (vat, "RO" + vat):
            partner = partner_obj.search(
                [
                    ("vat", "=ilike", variant),
                    *partner_obj._check_company_domain(company),
                ],
                order="is_company desc, id",
                limit=1,
            )
            if partner:
                return partner.commercial_partner_id
        return partner_obj

    @api.model
    def _l10n_ro_edi_autoinvoice_journal(self, company, partner):
        """Return ``(journal, dedicated)``.

        The dedicated journal is the sale journal of sequence type
        ``autoinv1`` configured for the customer. The fields come from the RO
        accounting modules, which this one does not depend on: without them,
        or without a journal for this customer, the first sale journal is
        used and the invoice is left in draft."""
        journal_obj = self.env["account.journal"]
        company_domain = [
            *journal_obj._check_company_domain(company),
            ("type", "=", "sale"),
        ]
        if partner and {"l10n_ro_partner_id", "l10n_ro_sequence_type"} <= set(
            journal_obj._fields
        ):
            journal = journal_obj.search(
                [
                    *company_domain,
                    ("l10n_ro_sequence_type", "=", "autoinv1"),
                    (
                        "l10n_ro_partner_id.commercial_partner_id",
                        "=",
                        partner.commercial_partner_id.id,
                    ),
                ],
                limit=1,
            )
            if journal:
                return journal, True
        return journal_obj.search(company_domain, order="sequence, id", limit=1), False

    @api.model
    def _l10n_ro_edi_create_autoinvoice(
        self, company, xml_bytes, file_name, index, document_vals=None
    ):
        """Create the sale invoice for an autofactura found in the SPV.

        In the customer's dedicated journal the invoice keeps the number the
        customer gave it and is posted; anywhere else it stays in draft. It is
        marked as validated in the SPV, so it is never sent again."""
        move_obj = self.with_company(company)
        existing = move_obj.search(
            [("company_id", "=", company.id), ("l10n_ro_edi_index", "=", index)],
            limit=1,
        )
        if existing:
            return existing

        partner = self._l10n_ro_edi_partner_from_vat(
            company, self._l10n_ro_edi_autoinvoice_customer_vat(company, xml_bytes)
        )
        journal, dedicated = self._l10n_ro_edi_autoinvoice_journal(company, partner)
        if not journal:
            raise UserError(
                self.env._("There is no sale journal to import the self-invoice in.")
            )
        move = move_obj.create(
            {
                "company_id": company.id,
                "move_type": "out_invoice",
                "journal_id": journal.id,
                "partner_id": partner.id,
            }
        )
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": file_name,
                    "raw": xml_bytes,
                    "mimetype": "application/xml",
                    "res_model": "account.move",
                    "res_id": move.id,
                }
            )
        )
        move.with_context(
            l10n_ro_autoinvoice_partner_id=partner.id
        )._extend_with_attachments(move._to_files_data(attachment))

        move.l10n_ro_edi_index = index
        self.env["l10n_ro_edi.document"].sudo().create(
            {
                "invoice_id": move.id,
                "state": "invoice_validated",
                **(document_vals or {}),
            }
        )

        if not dedicated:
            move.message_post(
                body=self.env._(
                    "Self-invoice issued by the customer in our name. No"
                    " self-invoicing journal is configured for this customer,"
                    " so it was left in draft."
                )
            )
            return move

        # The legal number is the one the customer gave the document.
        if move.ref and move.name in (False, "/"):
            move.name = move.ref
        try:
            with self.env.cr.savepoint():
                move.action_post()
        except (UserError, ValidationError) as e:
            move.invalidate_recordset()
            move.message_post(
                body=self.env._(
                    "Self-invoice issued by the customer in our name, left in"
                    " draft: %s",
                    e,
                )
            )
        return move

    @api.model
    def _l10n_ro_edi_process_autoinvoice_messages(self, messages):
        company = self.env.company
        for message in messages:
            answer = message["answer"]
            signature = answer.get("signature") or {}
            invoice_name = (answer["invoice"].get("name") or message["id"]).replace(
                "/", "_"
            )
            document_vals = {"key_download": message["id"]}
            if signature:
                document_vals.update(
                    {
                        "key_signature": signature["key_signature"],
                        "key_certificate": signature["key_certificate"],
                        "attachment": base64.b64encode(signature["attachment_raw"]),
                    }
                )
            move = self._l10n_ro_edi_create_autoinvoice(
                company,
                answer["invoice"]["attachment_raw"],
                f"ciusro_{invoice_name}.xml",
                message["id_solicitare"],
                document_vals=document_vals,
            )
            move.message_post(
                body=self.env._("Synchronized with SPV from message %s", message["id"])
            )

    def action_send_and_print_anaf(self):
        self.env["account.move.send"]._check_move_constraints(self)
        return {
            "name": self.env._("Send"),
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

    @api.model
    def _l10n_ro_edi_send_invoice_anaf_cron(self):
        account_move_send_model = self.env["account.move.send"]
        ro_companies = (
            self.env["res.company"]
            .sudo()
            .search(
                [
                    ("l10n_ro_edi_access_token", "!=", False),
                    ("l10n_ro_edi_residence", "!=", False),
                ]
            )
        )
        for company in ro_companies:
            days = company.l10n_ro_edi_residence
            date = fields.Date.today() - timedelta(days=days)
            invoices = self.env["account.move"].search(
                [
                    ("l10n_ro_edi_state", "=", False),
                    ("move_type", "!=", "entry"),
                    ("state", "=", ("posted")),
                    ("invoice_date", "<=", date),
                    ("invoice_date", ">=", date - timedelta(days=7)),
                    ("partner_id.country_id.code", "=", "RO"),
                    ("company_id", "=", company.id),
                ]
            )
            to_send_invoices = invoices.filtered(
                lambda move: account_move_send_model._is_ro_edi_applicable(move)
            )
            batch_model = self.env["account.move.send.batch.wizard"].with_context(
                l10n_ro_send_to_anaf=True
            )
            batch_wizard = batch_model.create({"move_ids": to_send_invoices.ids})
            batch_wizard.action_send_and_print()

    @api.model
    def _l10n_ro_edi_fetch_invoice_status_cron(self):
        ro_companies = (
            self.env["res.company"]
            .sudo()
            .search([("l10n_ro_edi_access_token", "!=", False)])
        )
        for company in ro_companies:
            invoices = (
                self.env["account.move"]
                .with_company(company)
                .search(
                    [
                        ("l10n_ro_edi_state", "=", "invoice_sent"),
                        ("state", "=", "posted"),
                        ("company_id", "=", company.id),
                    ]
                )
            )
            if not invoices:
                continue
            try:
                invoices._l10n_ro_edi_fetch_invoice_sent_documents()
            except UserError as e:
                _logger.warning(
                    "ANAF status fetch failed for company %s: %s", company.id, e
                )
