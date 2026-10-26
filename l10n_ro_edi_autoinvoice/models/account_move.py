# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import re

import requests
from lxml import etree

from odoo import api, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.l10n_ro_edi.models.utils import make_efactura_request


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _l10n_ro_edi_process_invoice_accepted_messages(
        self, sent_invoices_accepted_messages
    ):
        # A self-invoice listed as sent is not one of ours: take it out
        # before the standard matching on our own invoices.
        kept = self._l10n_ro_edi_split_autoinvoice_messages(
            sent_invoices_accepted_messages, received=False
        )
        if kept:
            return super()._l10n_ro_edi_process_invoice_accepted_messages(kept)

    @api.model
    def _l10n_ro_edi_process_bill_messages(self, received_bills_messages):
        # Self-invoices issued by customers in our name are sales, not bills.
        kept = self._l10n_ro_edi_split_autoinvoice_messages(
            received_bills_messages, received=True
        )
        if kept:
            return super()._l10n_ro_edi_process_bill_messages(kept)

    @api.model
    def _l10n_ro_edi_split_autoinvoice_messages(self, messages, received):
        """Process the self-invoices among ``messages`` and return the rest."""
        autoinvoices, kept = [], []
        for message in messages:
            if self._l10n_ro_edi_is_autoinvoice_message(message, received):
                autoinvoices.append(message)
            else:
                kept.append(message)
        if autoinvoices:
            self._l10n_ro_edi_process_autoinvoice_messages(autoinvoices)
        return kept

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
        ``autoinv1`` configured for the customer. Without one, the first sale
        journal is used and the invoice is left in draft."""
        journal_obj = self.env["account.journal"]
        company_domain = [
            *journal_obj._check_company_domain(company),
            ("type", "=", "sale"),
        ]
        if partner:
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

    # ------------------------------------------------------------------
    # Self-invoices we issue in a supplier's name (autoinv2)
    # ------------------------------------------------------------------

    def is_l10n_ro_autoinvoice(self):
        self.ensure_one()
        # Self-invoice we issue in a supplier's name: a purchase document on a
        # self-invoicing journal (l10n_ro_sequence_type == "autoinv2") tied to
        # the supplier.
        return (
            self.is_purchase_document()
            and self.journal_id.l10n_ro_sequence_type == "autoinv2"
            and bool(self.journal_id.l10n_ro_partner_id)
        )

    def _l10n_ro_edi_autofactura_upload(self, xml_data):
        """Upload a self-billed autoinvoice to the SPV with the right params.

        Native ``l10n_ro_edi._request_ciusro_send_invoice`` was written for
        customer invoices and mishandles self-issued documents (aligning here
        with the proven 16.0 ``l10n_ro_account_edi_ubl`` flow):

        * ``standard`` must be ``UBL`` for invoices and ``CN`` only for
          refunds; native sends any non-``out_invoice`` (incl. ``in_invoice``
          autoinvoices) as ``CN``.
        * self-issued documents need the ``autofactura=DA`` upload param,
          otherwise ANAF refuses a document whose supplier CIF differs from the
          uploading CIF.
        * the ``upload`` reply is in the ``respUploadFisier:v1`` namespace, not
          ``stareMesajFactura:v1``; native looked in the wrong namespace and
          returned an empty error string (the blank chatter bullet).

        :return: ``{'error': str}`` | ``{'key_loading': str | False}``
        """
        self.ensure_one()
        company = self.company_id
        is_refund = self.move_type in ("out_refund", "in_refund")
        is_b2b = self.partner_id.commercial_partner_id.is_company
        params = {
            "standard": "CN" if is_refund else "UBL",
            "cif": company.vat.replace("RO", ""),
            "autofactura": "DA",
        }
        result = make_efactura_request(
            session=requests,
            company=company,
            endpoint="upload" if is_b2b else "uploadb2c",
            params=params,
            data=xml_data,
        )
        if "error" in result:
            # A timeout means the SPV received it but returned no index yet.
            if "timeout" in result:
                return {"key_loading": False}
            return result

        root = etree.fromstring(result["content"])
        if root.get("ExecutionStatus") == "1":
            # Namespace-agnostic: read errorMessage off any element carrying it
            # so the real SPV rejection reason is no longer swallowed.
            messages = [el.get("errorMessage") for el in root.iter()]
            readable = "\n".join(m for m in messages if m)
            return {
                "error": readable
                or self.env._(
                    "SPV rejected the invoice without a readable error message. "
                    "Raw response: %s",
                    result["content"].decode(errors="replace"),
                )
            }
        return {"key_loading": root.get("index_incarcare")}

    def _l10n_ro_edi_send_invoice(self, xml_data):
        # EXTENDS l10n_ro_edi: for self-billed autoinvoices, replace the native
        # upload (wrong ``standard``, missing ``autofactura``, swallowed error)
        # with the autofactura-aware one, keeping the rest of the native
        # document/index/commit orchestration identical.
        self.ensure_one()
        if not self.is_l10n_ro_autoinvoice():
            return super()._l10n_ro_edi_send_invoice(xml_data)

        if errors := self._l10n_ro_edi_get_pre_send_errors(xml_data):
            self.message_post(
                body=self.env._(
                    "The invoice is not ready to be sent: %s", ", ".join(errors)
                )
            )
            return errors

        self.l10n_ro_edi_index = False
        self.env["res.company"]._with_locked_records(self)
        result = self._l10n_ro_edi_autofactura_upload(xml_data)
        if "error" in result:
            self.message_post(
                body=self.env._(
                    "Error when trying to send the e-Factura to the SPV: %s",
                    result["error"],
                )
            )
            return [result["error"]]

        self.env["l10n_ro_edi.document"].sudo().create(
            {
                "invoice_id": self.id,
                "state": "invoice_sent",
                "attachment": base64.b64encode(xml_data),
            }
        )
        if result["key_loading"]:
            self.l10n_ro_edi_index = result["key_loading"]
            self.message_post(
                body=self.env._(
                    "The e-Factura has been sent and is now being validated by "
                    "the SPV with index key: %s",
                    self.l10n_ro_edi_index,
                )
            )
        else:
            self.l10n_ro_edi_state = "invoice_not_indexed"
            self.message_post(
                body=self.env._(
                    "SPV failed to return with an index on time, synchronize "
                    "this invoice to recover the index and the status."
                )
            )

        # Mirror native l10n_ro_edi: persist the sent document + index before the
        # SPV round-trip so a later failure in the same batch cannot roll it back.
        if self._can_commit():
            self.env.cr.commit()  # pylint: disable=invalid-commit
        return None
